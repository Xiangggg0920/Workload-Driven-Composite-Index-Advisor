"""3A preparation tests: database generation/creation/loading is ALWAYS mocked."""
import csv
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

from psycopg.conninfo import conninfo_to_dict

from dataset import prepare_sf1 as sf1


def plan():
    return {"mode": "inspection_only", "blockers": [],
            "server": {"data_directory": str(sf1.ROOT)},
            "smoke_locale": ["UTF8", "Chinese (Traditional)_Taiwan.950", "Chinese (Traditional)_Taiwan.950", "c"],
            "smoke_before": {"counts": [15000, 60175]}, "protected_hashes": {"x": "hash"},
            "database_created": False, "sf1_generated": False, "data_loaded": False}


class Sf1PreparationTests(unittest.TestCase):
    def test_default_cli_never_generates_creates_or_loads(self):
        with patch.object(sf1, "preflight", return_value=plan()), patch.object(sf1, "execute_plan") as execute:
            with redirect_stdout(output := io.StringIO()):
                code = sf1.main([])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["mode"], "inspection_only")
        execute.assert_not_called()

    def test_execution_needs_exact_confirmation_before_any_preflight(self):
        for args in (["--execute"], ["--execute", "--confirm-database", "advisor_smoke"],
                     ["--confirm-database", "advisor_benchmark"]):
            with self.subTest(args=args), patch.object(sf1, "preflight") as inspect:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    sf1.main(args)
                self.assertEqual(error.exception.code, 2)
                inspect.assert_not_called()

    def test_api_wrong_confirmation_does_not_generate(self):
        with patch.object(sf1.tpch, "generate") as generate, self.assertRaises(ValueError):
            sf1.execute_plan(plan(), "advisor_smoke")
        generate.assert_not_called()

    def test_blockers_never_generate(self):
        for reason in ("target exists", "source exists", "insufficient disk space"):
            p = plan()
            p["blockers"] = [reason]
            with patch.object(sf1.tpch, "generate") as generate, self.assertRaises(RuntimeError):
                sf1.execute_plan(p, sf1.TARGET)
            generate.assert_not_called()

    def test_existing_report_never_overwritten(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "existing.json"
            output.write_text("keep", encoding="utf-8")
            with patch.object(sf1, "preflight") as inspect:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    sf1.main(["--output", str(output)])
            inspect.assert_not_called()
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")

    def test_preflight_blockers_produce_nonzero_json(self):
        p = plan()
        p["blockers"] = ["target already exists"]
        with patch.object(sf1, "preflight", return_value=p), redirect_stdout(output := io.StringIO()):
            self.assertEqual(sf1.main([]), 2)
        self.assertEqual(json.loads(output.getvalue())["blockers"], p["blockers"])

    def test_volume_space_checks_deduplicate_shared_volume(self):
        usage = type("Usage", (), {"total": 100 * sf1.GIB, "free": 30 * sf1.GIB})()
        with patch.object(sf1.shutil, "disk_usage", return_value=usage) as disk:
            result = sf1.check_space([sf1.ROOT, sf1.ROOT / "data"], 20 * sf1.GIB)
        self.assertEqual(len(result), 1)
        disk.assert_called_once()
        self.assertTrue(next(iter(result.values()))["sufficient"])

    def test_validate_csv_checks_shape_count_and_digest(self):
        with TemporaryDirectory() as directory:
            source = Path(directory)
            for table, width in sf1.EXPECTED_COLUMNS.items():
                with (source / f"{table}.csv").open("w", encoding="utf-8", newline="") as stream:
                    csv.writer(stream).writerow(["a,b"] * width)
            with patch.object(sf1, "EXPECTED_ROWS", {"orders": 1, "lineitem": 1}):
                result = sf1.validate_csv(source)
            self.assertEqual(result["lineitem"]["rows"], 1)
            self.assertEqual(len(result["orders"]["sha256"]), 64)
            self.assertGreater(result["orders"]["bytes"], 0)

    def test_wrong_csv_shape_and_scale_rejected(self):
        with TemporaryDirectory() as directory:
            source = Path(directory)
            path = source / "orders.csv"
            path.write_text("1,2\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "column count"):
                sf1.validate_csv(source)
            path.write_text(",".join(["1"] * 9) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Wrong scale"):
                sf1.validate_csv(source)

    def test_invalid_generated_scale_stops_before_database_creation(self):
        with patch.object(sf1.tpch, "generate"), patch.object(sf1, "validate_csv", side_effect=ValueError("wrong scale")):
            with patch.object(sf1, "create_target") as create, self.assertRaises(ValueError):
                sf1.execute_plan(plan(), sf1.TARGET)
        create.assert_not_called()

    def run_mocked_execution(self, *, load_error=None):
        p = plan()
        with patch.object(sf1.tpch, "generate") as generate, patch.object(sf1, "validate_csv", return_value={}), \
             patch.object(sf1, "smoke_snapshot", return_value=p["smoke_before"]), \
             patch.object(sf1, "check_space", return_value={"C": {"sufficient": True}}), \
             patch.object(sf1, "create_target") as create, \
             patch.object(sf1.tpch, "load", side_effect=load_error) as load, \
             patch.object(sf1, "verify_target", return_value={"counts": [1500000, 6001215]}), \
             patch.object(sf1, "protected_hashes", return_value=p["protected_hashes"]):
            if load_error:
                with self.assertRaises(RuntimeError):
                    sf1.execute_plan(p, sf1.TARGET)
            else:
                sf1.execute_plan(p, sf1.TARGET)
        return p, generate, create, load

    def test_success_explicitly_targets_benchmark_without_changing_pgdatabase(self):
        with patch.dict(os.environ, {"PGDATABASE": "advisor_smoke"}):
            p, generate, create, load = self.run_mocked_execution()
            self.assertEqual(os.environ["PGDATABASE"], "advisor_smoke")
        self.assertTrue(p["verified"])
        create.assert_called_once()
        self.assertEqual(generate.call_args.args[0], 1)
        self.assertEqual(conninfo_to_dict(load.call_args.args[1])["dbname"], "advisor_benchmark")

    def test_failed_load_records_created_database_without_auto_cleanup(self):
        p, _, create, _ = self.run_mocked_execution(load_error=RuntimeError("copy failed"))
        self.assertTrue(p["database_created"])
        self.assertFalse(p["data_loaded"])
        self.assertNotIn("verified", p)
        create.assert_called_once()

    def test_concurrent_target_appearance_refuses_create(self):
        connection = MagicMock()
        with patch.object(sf1.psycopg, "connect", return_value=connection), \
             patch.object(sf1, "read_rows", return_value=[(1,)]), self.assertRaises(RuntimeError):
            sf1.create_target(plan())
        connection.__enter__.return_value.cursor.assert_not_called()

    def test_create_uses_clean_template_and_inherited_locale(self):
        connection = MagicMock()
        with patch.object(sf1.psycopg, "connect", return_value=connection), \
             patch.object(sf1, "read_rows", return_value=[]):
            sf1.create_target(plan())
        command = connection.__enter__.return_value.cursor.return_value.__enter__.return_value.execute.call_args.args[0].as_string()
        self.assertIn('CREATE DATABASE "advisor_benchmark"', command)
        self.assertIn("TEMPLATE template0", command)
        self.assertIn("LC_COLLATE", command)
        self.assertNotIn("advisor_smoke", command)
        self.assertNotIn("INDEX", command)

    def test_verify_wrong_target_or_indexes_fail(self):
        rows = [[("wrong_database",)], [(1500000, 6001215)], [],
                [("lineitem", 16), ("orders", 9)], [], []]
        with patch.object(sf1.psycopg, "connect"), patch.object(sf1, "read_rows", side_effect=rows):
            with self.assertRaises(RuntimeError):
                sf1.verify_target()


if __name__ == "__main__":
    unittest.main()
