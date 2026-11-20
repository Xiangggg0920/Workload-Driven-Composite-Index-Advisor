"""No real DDL: all mutation/measurement integration uses an in-memory fake DB."""
import copy
from collections import Counter, defaultdict
from contextlib import contextmanager, redirect_stderr
from dataclasses import asdict
import io
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from advisor.statistics import ColumnStats, TableStats
from analysis.sf1_budget import simulate
from strategy_benchmark.database import Database, OverBudget, SafetyError, owned
from strategy_benchmark.engine import (Journal, annotate, dry_run, execute, paired_comparisons,
                                       recovery, validate_journal)
from strategy_benchmark.main import main
from strategy_benchmark.plan import (ROOT, build_plan, controls, create_ddl, ddl_manifest, digest,
                                     pack_control, prefix_overlap, seal, validate_plan)
from workload.validate_benchmark20 import audit_advisor

SOURCE = (ROOT / "workload/benchmark20.sql").read_bytes().decode("utf-8-sig")


def fixture(rounds=4):
    schema = (ROOT / "dataset/schema.sql").read_text(encoding="utf-8")
    distinct = {"o_orderkey": 1500000, "o_custkey": 100000, "o_clerk": 1000,
        "o_orderpriority": 5, "o_orderstatus": 3, "l_orderkey": 1500000,
        "l_returnflag": 3, "l_linestatus": 2, "l_shipmode": 7, "l_suppkey": 10000}
    tables = {}
    for table, body in re.findall(r"CREATE TABLE tpch\.(\w+)\s*\((.*?)\);", schema, re.S):
        names = re.findall(r"^\s+([ol]_\w+)\s+", body, re.M)
        tables[table] = TableStats("tpch", table, 1500000 if table == "orders" else 6001215,
            226689024 if table == "orders" else 995819520,
            {name: ColumnStats(distinct.get(name, 2500), 0, 8) for name in names})
    audit, parsed, candidates = audit_advisor(SOURCE, tables)
    report = {**simulate(parsed.queries, tables, candidates, audit),
              "catalog": {n: asdict(t) for n, t in tables.items()},
              "workload_sha256": __import__("hashlib").sha256(SOURCE.encode()).hexdigest()}
    acceptance = {"database": "advisor_benchmark", "passed": True, "checks": {"ok": True},
                  "orders": {"rows": 1500000}, "lineitem": {"rows": 6001215}}
    environment = {"identity": {"database": "advisor_benchmark", "database_oid": 123,
        "system_identifier": "test-system", "server_version": "17.12", "address": "::1/128", "port": 5432, "role": "tester"},
        "indexes": [], "tables": [{"oid": 1, "name": "lineitem", "columns": list(tables["lineitem"].columns)},
                                    {"oid": 2, "name": "orders", "columns": list(tables["orders"].columns)}],
        "settings": {"jit": "on"}, "column_statistics_sha256": "stats", "active_other_backends": [],
        "disk_free_bytes": 50 * 1024**3}
    plan = build_plan(SOURCE, report, acceptance, environment, "123456abcdef", "a" * 32, rounds=rounds)
    return plan, tables


def metadata(spec, tag, oid=99):
    return {"oid": oid, "schema": spec["schema"], "name": spec["name"], "table_schema": "tpch",
        "table": spec["table"], "table_oid": 2, "method": "btree", "columns": spec["columns"][:],
        "nkeys": len(spec["columns"]), "natts": len(spec["columns"]), "unique": False,
        "primary": False, "valid": True, "ready": True, "constraint": False,
        "predicate": None, "expressions": None, "comment": tag, "owner": "tester",
        "main_bytes": spec["estimated_bytes"], "total_bytes": spec["estimated_bytes"],
        "definition": create_ddl(spec)}


class FakeDatabase:
    def __init__(self, plan, shared, allow_write=False, over_budget=False):
        self.plan, self.shared, self.allow_write = plan, shared, allow_write
        self.identity = copy.deepcopy(plan["database"])
        self.over_budget = over_budget
        self.conn = object()
        self.guarded = False

    def close(self):
        pass

    def capture(self):
        result = copy.deepcopy(self.plan["environment"])
        result["indexes"] = self.indexes()
        return result

    def indexes(self):
        return copy.deepcopy(self.shared["indexes"])

    def settings(self):
        return self.plan["environment"]["settings"]

    def statistics_signature(self):
        return "stats"

    def maintenance(self):
        return []

    def acquire(self):
        if not self.allow_write:
            raise AssertionError("dry-run tried to acquire execution lock")

    def release(self):
        pass

    @contextmanager
    def guard_data(self):
        self.guarded = True
        try:
            yield
        finally:
            self.guarded = False

    def data_signature(self):
        return {"orders": ["1500000", "a", "b"], "lineitem": ["6001215", "c", "d"]}

    def build(self, specs, budget, tag):
        if not self.allow_write:
            raise AssertionError("dry-run tried to build")
        if specs and self.over_budget:
            over = metadata(specs[0], tag)
            over["main_bytes"] = budget + 8192
            raise OverBudget([over], budget)
        self.shared["indexes"] = [metadata(s, tag, i + 100) for i, s in enumerate(specs)]
        self.shared["builds"] += 1
        return self.indexes()

    def cleanup(self, entries, tag):
        if self.guarded:
            raise AssertionError("Cleanup while SHARE guard still held")
        self.shared["cleanup_attempts"] += 1
        if self.shared.get("cleanup_fail") and self.shared["indexes"]:
            raise RuntimeError("simulated cleanup connection failure")
        for index in self.shared["indexes"]:
            entry = next(e for e in entries if e["spec"]["name"] == index["name"])
            if not owned(index, entry, tag, "tester"):
                raise SafetyError("foreign index")
        names = [i["name"] for i in self.shared["indexes"]]
        self.shared["indexes"] = []
        return names


def fake_runner(connection, statements, report, config):
    for i, statement in enumerate(statements, 1):
        report["queries"].append({"number": i, "sql": statement.sql, "status": "ok", "warmup_runs": [],
            "measurements": [{"status": "ok", "execution_time_ms": 1, "shared_hit_blocks": 2,
                              "shared_read_blocks": 0, "query_plan": [{"Plan": {"Node Type": "Result"}}]}],
            "summary": {"execution_time_ms": {"mean": 1}, "shared_hit_blocks": {"mean": 2},
                        "shared_read_blocks": {"mean": 0}}})
    report["status"] = "ok"
    return report


class StrategyPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, cls.tables = fixture()

    def test_advisor_method_and_exact_3b_configuration_preserved(self):
        self.assertEqual(self.plan["configurations"]["100"]["advisor"]["selection_method"], "exact")
        self.assertEqual(self.plan["configurations"]["500"]["advisor"]["selection_method"], "marginal-greedy")
        self.assertEqual(self.plan["supported_queries"], list(range(1, 17)))

    def test_controls_use_only_relevant_columns_and_no_permutation_duplication(self):
        pool = controls(self.tables)
        self.assertEqual(len(pool["single"]), 17)
        keys = [(r["table"], tuple(sorted(r["columns"]))) for r in pool["suboptimal"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("tpch.lineitem(l_commitdate)", [r["label"] for r in pool["single"]])
        for records in pool.values():
            for record in records:
                self.assertTrue(record["generated_by_queries"])
                self.assertTrue(record["referenced_by_queries"])
                self.assertTrue(set(record["columns"]) <= set(self.tables[record["table"]].columns))

    def test_source_order_not_intentionally_reversed(self):
        records = controls(self.tables)["suboptimal"]
        by_label = {r["label"]: r for r in records}
        self.assertIn("tpch.orders(o_orderstatus, o_orderdate)", by_label)
        self.assertNotIn("tpch.orders(o_orderdate, o_orderstatus)", by_label)
        self.assertIn("tpch.lineitem(l_shipdate, l_discount, l_quantity)", by_label)

    def test_controls_fit_estimates_and_exclude_prefix_redundancy(self):
        for budget in self.plan["configurations"].values():
            for strategy in ("single", "suboptimal"):
                selected = budget[strategy]["indexes"]
                for i, first in enumerate(selected):
                    self.assertFalse(any(prefix_overlap(first, other) for other in selected[i + 1:]))

    def test_schedule_is_balanced_and_all_queries_equal_within_block(self):
        positions, transitions, groups = defaultdict(Counter), Counter(), defaultdict(list)
        for cell in self.plan["schedule"]:
            positions[(cell["budget_mib"], cell["strategy"])][cell["position"]] += 1
            groups[(cell["round"], cell["budget_mib"])].append(cell)
        for counter in positions.values():
            self.assertEqual(counter, Counter({1: 1, 2: 1, 3: 1, 4: 1}))
        for cells in groups.values():
            self.assertEqual(len({tuple(c["query_order"]) for c in cells}), 1)
            self.assertEqual(sorted(cells[0]["query_order"]), list(range(1, 21)))
            if cells[0]["budget_mib"] == 100:
                transitions.update((a["strategy"], b["strategy"]) for a, b in zip(cells, cells[1:]))
        self.assertEqual(len(transitions), 12)
        self.assertEqual(set(transitions.values()), {1})

    def test_plan_hash_tampering_and_missing_cells_fail(self):
        broken = copy.deepcopy(self.plan)
        broken["schedule"].pop()
        with self.assertRaises(ValueError):
            validate_plan(broken, SOURCE)
        broken["plan_sha256"] = seal(broken)
        with self.assertRaisesRegex(ValueError, "schedule"):
            validate_plan(broken, SOURCE)

    def test_single_round_retains_exact_configurations_and_first_round_order(self):
        single, _ = fixture(rounds=1)
        self.assertEqual(len(single["schedule"]), 12)
        self.assertEqual(single["configurations"], self.plan["configurations"])
        self.assertEqual(single["schedule"], self.plan["schedule"][:12])
        self.assertFalse(single["schedule_policy"]["fully_counterbalanced"])
        self.assertTrue(self.plan["schedule_policy"]["fully_counterbalanced"])
        self.assertEqual(single["measurement"], {"warmup": 2, "repeats": 5, "statement_timeout_ms": 120000})
        validate_plan(single, SOURCE)

    def test_invalid_round_counts_and_incomplete_single_round_are_rejected(self):
        for rounds in (0, -1, True, 1.5):
            broken = copy.deepcopy(self.plan)
            broken["rounds"] = rounds
            broken["plan_sha256"] = seal(broken)
            with self.subTest(rounds=rounds), self.assertRaisesRegex(ValueError, "positive integer"):
                validate_plan(broken, SOURCE)
        broken, _ = fixture(rounds=1)
        broken["schedule"].pop()
        broken["plan_sha256"] = seal(broken)
        with self.assertRaisesRegex(ValueError, "schedule"):
            validate_plan(broken, SOURCE)

    def test_partial_four_round_cycles_are_allowed_and_labeled(self):
        partial, _ = fixture(rounds=2)
        self.assertEqual(len(partial["schedule"]), 24)
        self.assertFalse(partial["schedule_policy"]["fully_counterbalanced"])
        validate_plan(partial, SOURCE)

    def test_single_round_cannot_claim_full_order_balance(self):
        single, _ = fixture(rounds=1)
        single["schedule_policy"]["fully_counterbalanced"] = True
        single["plan_sha256"] = seal(single)
        with self.assertRaisesRegex(ValueError, "balance label"):
            validate_plan(single, SOURCE)

    def test_names_are_unique_short_and_ddl_is_quoted(self):
        specs = [s for c in self.plan["schedule"] for s in c["indexes"]]
        names = [s["name"] for s in specs]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(len(name.encode()) <= 63 for name in names))
        self.assertIn('ON "tpch".', ddl_manifest(self.plan))


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.plan, _ = fixture()
        self.spec = next(s for c in self.plan["schedule"] for s in c["indexes"])
        self.entry = {"spec": self.spec, "oid": 99, "state": "committed"}
        self.index = metadata(self.spec, self.plan["ownership_tag"])

    def test_prefix_alone_wrong_oid_definition_tag_owner_constraint_all_refused(self):
        self.assertTrue(owned(self.index, self.entry, self.plan["ownership_tag"], "tester"))
        for key, value in (("oid", 101), ("comment", "foreign"), ("owner", "another"),
                           ("columns", ["unrelated"]), ("constraint", True), ("unique", True),
                           ("predicate", "a > 0"), ("valid", False), ("method", "hash")):
            with self.subTest(key=key):
                changed = {**self.index, key: value}
                self.assertFalse(owned(changed, self.entry, self.plan["ownership_tag"], "tester"))

    def test_committed_before_journal_oid_flush_is_recoverable_by_atomic_tag(self):
        pending = {"spec": self.spec, "oid": None, "state": "pending"}
        self.assertTrue(owned(self.index, pending, self.plan["ownership_tag"], "tester"))
        self.assertFalse(owned({**self.index, "comment": None}, pending, self.plan["ownership_tag"], "tester"))

    def test_readonly_connection_refuses_write_before_sending_sql(self):
        db = Database.__new__(Database)
        db.allow_write = False
        db.conn = MagicMock()
        with self.assertRaises(SafetyError):
            db.write("CREATE INDEX not_allowed")
        db.conn.execute.assert_not_called()

    def test_real_cleanup_implementation_checks_all_before_any_drop(self):
        db = Database.__new__(Database)
        db.allow_write = True
        db.conn = MagicMock()
        db.identity = {"role": "tester"}
        db.indexes = lambda: [{**self.index, "comment": "foreign"}]
        commands = []
        db.write = commands.append
        with self.assertRaises(SafetyError):
            db.cleanup([self.entry], self.plan["ownership_tag"])
        self.assertFalse(any(c.startswith("DROP") for c in commands))

    def test_saved_definition_or_table_oid_change_is_refused(self):
        entry = {**self.entry, "definition": self.index["definition"], "table_oid": self.index["table_oid"]}
        self.assertFalse(owned({**self.index, "definition": "different"}, entry, self.plan["ownership_tag"], "tester"))
        self.assertFalse(owned({**self.index, "table_oid": 999}, entry, self.plan["ownership_tag"], "tester"))

    def test_cleanup_validates_later_foreign_entry_before_dropping_first(self):
        other = next(s for c in self.plan["schedule"] for s in c["indexes"] if s["name"] != self.spec["name"])
        foreign = metadata(other, "foreign", 100)
        db = Database.__new__(Database)
        db.allow_write, db.conn, db.identity = True, MagicMock(), {"role": "tester"}
        db.indexes = lambda: [self.index, foreign]
        commands = []
        db.write = commands.append
        with self.assertRaises(SafetyError):
            db.cleanup([self.entry, {"spec": other, "state": "committed", "oid": 100}], self.plan["ownership_tag"])
        self.assertFalse(any(command.startswith("DROP") for command in commands))

    def test_valid_cleanup_uses_restrict_and_only_journaled_name(self):
        db = Database.__new__(Database)
        db.allow_write, db.conn, db.identity = True, MagicMock(), {"role": "tester"}
        db.indexes = lambda: [self.index]
        commands = []
        db.write = commands.append
        self.assertEqual(db.cleanup([self.entry], self.plan["ownership_tag"]), [self.spec["name"]])
        drops = [command for command in commands if command.startswith("DROP")]
        self.assertEqual(len(drops), 1)
        self.assertIn(self.spec["name"], drops[0])
        self.assertTrue(drops[0].endswith(" RESTRICT;"))

    def test_real_build_overbudget_rolls_back_and_does_not_add_more(self):
        db = Database.__new__(Database)
        db.allow_write = True
        db.conn = MagicMock()
        db.identity = {"role": "tester"}
        db.indexes = MagicMock(side_effect=[[], [self.index]])
        db.write = MagicMock()
        with self.assertRaises(OverBudget):
            db.build([self.spec, self.spec], 1, self.plan["ownership_tag"])
        self.assertEqual(sum(c.args[0].startswith("CREATE INDEX") for c in db.write.call_args_list), 1)
        self.assertIs(db.conn.transaction.return_value.__exit__.call_args.args[0], OverBudget)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.plan, _ = fixture()
        self.shared = {"indexes": [], "builds": 0, "cleanup_attempts": 0}

    def factory(self, **kwargs):
        return FakeDatabase(self.plan, self.shared, **kwargs)

    def test_dry_run_never_builds_locks_or_runs_measurement(self):
        db = self.factory(allow_write=False)
        result = dry_run(self.plan, SOURCE, db)
        self.assertEqual(result["status"], "dry_run_ok")
        self.assertFalse(result["ddl_executed"])
        self.assertEqual(self.shared["builds"], 0)

    def test_execute_wrong_approval_never_opens_connection(self):
        with TemporaryDirectory() as directory, patch("strategy_benchmark.engine.Database") as connect:
            with self.assertRaises(SafetyError):
                execute(self.plan, SOURCE, Path(directory) / "run", "wrong", database_factory=connect)
            connect.assert_not_called()

    def test_full_fake_run_keeps_20_and_16_and_restores_empty_inventory(self):
        with TemporaryDirectory() as directory:
            result = execute(self.plan, SOURCE, Path(directory) / "run", self.plan["plan_sha256"],
                             database_factory=self.factory, runner=fake_runner)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(len(result["cells"]), 48)
            self.assertEqual(self.shared["indexes"], [])
            self.assertTrue(all(c["summaries"]["full20"]["query_count"] == 20 for c in result["cells"]))
            self.assertTrue(all(c["summaries"]["advisor16"]["query_count"] == 16 for c in result["cells"]))
            self.assertTrue(all(c["full20_speedup"] == 1 for c in result["comparisons"]))

    def test_single_round_fake_execution_preserves_measurement_contract_and_results(self):
        self.plan, _ = fixture(rounds=1)
        configs = []

        def recording_runner(connection, statements, report, config):
            configs.append((len(statements), asdict(config)))
            return fake_runner(connection, statements, report, config)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "run"
            result = execute(self.plan, SOURCE, path, self.plan["plan_sha256"],
                database_factory=self.factory, runner=recording_runner)
            self.assertEqual(len(result["cells"]), 12)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(configs, [(20, self.plan["measurement"])] * 12)
            self.assertEqual(len(list(path.glob("*.runner.json"))), 12)
            self.assertFalse(list(path.glob("*.tmp")))
            for cell in result["cells"]:
                raw = json.loads((path / (cell["id"] + ".json")).read_text(encoding="utf-8"))
                self.assertEqual(raw["summaries"]["full20"]["query_count"], 20)
                self.assertEqual(raw["summaries"]["advisor16"]["query_count"], 16)
                self.assertTrue(raw["capacity_check"]["passed"])
                self.assertTrue(raw["valid_for_comparison"])
            self.assertEqual(self.shared["indexes"], [])

    def test_overbudget_is_infeasible_not_a_pass_or_zero_latency(self):
        factory = lambda **kwargs: FakeDatabase(self.plan, self.shared, over_budget=True, **kwargs)
        with TemporaryDirectory() as directory:
            result = execute(self.plan, SOURCE, Path(directory) / "run", self.plan["plan_sha256"],
                             database_factory=factory, runner=fake_runner)
        self.assertEqual(result["status"], "complete_with_infeasible_configurations")
        self.assertFalse(result["all_configurations_budget_feasible"])
        failed = [c for c in result["comparisons"] if c["status"] == "budget_exceeded"]
        self.assertTrue(failed)
        self.assertTrue(all(c["full20_speedup"] is None for c in failed))
        self.assertEqual(self.shared["indexes"], [])

    def test_runner_interrupt_preserves_raw_and_cleanup(self):
        def interrupt(*args):
            raise KeyboardInterrupt("test")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run"
            with self.assertRaises(KeyboardInterrupt):
                execute(self.plan, SOURCE, path, self.plan["plan_sha256"], database_factory=self.factory, runner=interrupt)
            journal = json.loads((path / "journal.json").read_text(encoding="utf-8"))
            self.assertEqual(journal["status"], "failed")
            self.assertTrue(list(path.glob("*.runner.json")))
            self.assertEqual(self.shared["indexes"], [])

    def test_failed_cleanup_leaves_durable_recovery_instructions(self):
        self.shared["cleanup_fail"] = True
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run"
            with self.assertRaises(RuntimeError):
                execute(self.plan, SOURCE, path, self.plan["plan_sha256"], database_factory=self.factory, runner=fake_runner)
            data = json.loads((path / "journal.json").read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "cleanup_required")
            self.assertTrue(data["entries"])
            journal = Journal(path, data)
            preview = recovery(self.plan, journal, self.factory(allow_write=False))
            self.assertFalse(preview["ddl_executed"])
            self.shared["cleanup_fail"] = False
            recovery(self.plan, journal, self.factory(allow_write=True), execute_cleanup=True)
            self.assertEqual(self.shared["indexes"], [])

    def test_per_run_plan_index_usage_and_original_ids_are_preserved(self):
        cell = next(c for c in self.plan["schedule"] if c["indexes"])
        index = metadata(cell["indexes"][0], self.plan["ownership_tag"])
        index["managed_this_cell"] = True
        from benchmark.sql import split_workload
        raw = fake_runner(None, [split_workload(SOURCE)[n - 1] for n in cell["query_order"]], {"queries": []}, None)
        raw["queries"][0]["measurements"][0]["query_plan"][0]["Plan"] = {
            "Node Type": "Bitmap Heap Scan", "Plans": [{"Node Type": "Bitmap Index Scan", "Index Name": index["name"]}]}
        result = annotate(raw, cell, [index], list(range(1, 17)))
        self.assertEqual(result["queries"][0]["number"], cell["query_order"][0])
        self.assertEqual(result["queries"][0]["measurements"][0]["used_indexes"][0]["oid"], index["oid"])
        self.assertEqual(result["summaries"]["advisor16"]["query_count"], 16)

    def test_foreign_index_in_recovery_never_reaches_cleanup(self):
        cell = next(c for c in self.plan["schedule"] if c["indexes"])
        entry = {"spec": cell["indexes"][0], "state": "pending", "oid": None}
        self.shared["indexes"] = [metadata(entry["spec"], "foreign")]
        with TemporaryDirectory() as directory:
            journal = Journal(directory, {"plan_sha256": self.plan["plan_sha256"], "run_id": self.plan["run_id"],
                "ownership_tag": self.plan["ownership_tag"], "database": self.plan["database"], "entries": [entry]})
            with self.assertRaises(SafetyError):
                recovery(self.plan, journal, self.factory(allow_write=True), execute_cleanup=True)
        self.assertEqual(self.shared["cleanup_attempts"], 0)


if __name__ == "__main__":
    unittest.main()
