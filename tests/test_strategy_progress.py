"""48-cell progress simulations and fake-controller checks; no PostgreSQL."""
import copy
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import asdict
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from strategy_benchmark.engine import execute
from strategy_benchmark.main import main
from strategy_benchmark.progress import LiveProgress
from tests.test_strategy_benchmark import FakeDatabase, SOURCE, fake_runner, fixture


class Terminal(io.StringIO):
    def isatty(self):
        return True


def event(plan, cell, completed, status):
    return {"rounds": plan["rounds"], "round": cell["round"],
            "strategy": cell["strategy"], "budget_mib": cell["budget_mib"],
            "completed": completed, "total": len(plan["schedule"]), "status": status}


def simulate(plan, progress):
    for i, cell in enumerate(plan["schedule"]):
        progress(event(plan, cell, i, "building"))
        progress(event(plan, cell, i, "measuring"))
        progress(event(plan, cell, i + 1, "cell_ok"))
    progress(event(plan, plan["schedule"][-1], 48, "complete"))


def complete_runner(connection, statements, report, config):
    raw = fake_runner(connection, statements, report, config)
    for query in raw["queries"]:
        sample = query["measurements"][0]
        for key, phase, count in (("warmup_runs", "warmup", config.warmup),
                                  ("measurements", "measurement", config.repeats)):
            query[key] = [{**copy.deepcopy(sample), "phase": phase, "iteration": i + 1,
                           "planning_time_ms": .5} for i in range(count)]
    return raw


class ProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, _ = fixture()

    def test_interactive_48_cells_show_round_strategy_budget_count_and_success(self):
        stream = Terminal()
        simulate(self.plan, LiveProgress(stream))
        text = stream.getvalue()
        for expected in ("\r", "48/48", "R4/4", "Baseline", "Single", "Suboptimal", "Advisor",
                         "100MiB", "500MiB", "1024MiB", "measuring", "complete"):
            self.assertIn(expected, text)
        self.assertTrue(text.endswith("\n"))

    def test_failed_event_does_not_claim_48_successes(self):
        stream = Terminal()
        progress = LiveProgress(stream)
        for i, cell in enumerate(self.plan["schedule"][:13]):
            progress(event(self.plan, cell, i + 1, "cell_ok"))
        progress(event(self.plan, self.plan["schedule"][13], 13, "failed"))
        self.assertIn("13/48", stream.getvalue())
        self.assertIn("failed", stream.getvalue())
        self.assertNotIn("48/48", stream.getvalue())
        self.assertTrue(stream.getvalue().endswith("\n"))

    def test_ui_exception_falls_back_to_text_and_finishes_48_events(self):
        stream = Terminal()
        progress = LiveProgress(stream)
        with patch.object(progress, "_render", side_effect=RuntimeError("UI failed")) as render:
            simulate(self.plan, progress)
        self.assertEqual(render.call_count, 1)
        self.assertFalse(progress.live)
        self.assertIn("using text output", stream.getvalue())
        self.assertIn("48/48", stream.getvalue())
        self.assertIn("complete", stream.getvalue())

    def test_noninteractive_terminal_uses_lines_without_control_codes(self):
        stream = io.StringIO()
        simulate(self.plan, LiveProgress(stream))
        self.assertNotIn("\r", stream.getvalue())
        self.assertNotIn("\x1b", stream.getvalue())
        self.assertIn("48/48", stream.getvalue().splitlines()[-1])

    def test_terminal_detection_failure_uses_text(self):
        stream = Terminal()
        with patch.object(stream, "isatty", side_effect=OSError("no console")):
            progress = LiveProgress(stream)
        simulate(self.plan, progress)
        self.assertNotIn("\r", stream.getvalue())
        self.assertIn("48/48", stream.getvalue())

    def test_broken_stream_and_invalid_event_never_raise(self):
        stream = MagicMock()
        stream.isatty.return_value = True
        stream.write.side_effect = BrokenPipeError("closed")
        simulate(self.plan, LiveProgress(stream))
        LiveProgress(stream)({})
        stream = Terminal()
        stream.flush = MagicMock(side_effect=OSError("flush failed"))
        simulate(self.plan, LiveProgress(stream))

    def test_keyboard_interrupt_still_reaches_normal_stop_handling(self):
        progress = LiveProgress(Terminal())
        with patch.object(progress, "_render", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                progress(event(self.plan, self.plan["schedule"][0], 0, "building"))


class ControllerProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, _ = fixture()

    def run_fake(self, directory, progress=None, *, fail_at=None, over_budget=False):
        shared = {"indexes": [], "builds": 0, "cleanup_attempts": 0}
        dbs, configs, display_during_measurement = [], [], []
        methods = ("capture", "indexes", "settings", "statistics_signature", "maintenance",
                   "acquire", "release", "guard_data", "data_signature", "build", "cleanup", "close")
        active = False

        def factory(**kwargs):
            db = FakeDatabase(self.plan, shared, over_budget=over_budget, **kwargs)
            for name in methods:
                setattr(db, name, MagicMock(wraps=getattr(db, name)))
            dbs.append(db)
            return db

        def runner(connection, statements, report, config):
            nonlocal active
            active = True
            try:
                configs.append((len(statements), asdict(config)))
                if fail_at == len(configs):
                    raise RuntimeError("simulated measurement failure")
                return complete_runner(connection, statements, report, config)
            finally:
                active = False

        def observer(update):
            display_during_measurement.append(active)
            progress(update)

        result = execute(self.plan, SOURCE, directory, self.plan["plan_sha256"],
                         database_factory=factory, runner=runner,
                         progress=observer if progress is not None else None)
        calls = [{name: getattr(db, name).call_count for name in methods} for db in dbs]
        self.assertFalse(any(display_during_measurement), "UI must stay outside the Runner measurement call")
        self.assertEqual(shared["indexes"], [])
        return result, configs, calls

    def test_ui_modes_preserve_48_results_measurements_and_database_call_counts(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, configs, calls = self.run_fake(root / "off")
            self.assertEqual(configs, [(20, self.plan["measurement"])] * 48)
            for mode in ("interactive", "noninteractive", "ui_error", "observer_error"):
                with self.subTest(mode=mode):
                    stream = io.StringIO() if mode == "noninteractive" else Terminal()
                    progress = LiveProgress(stream)
                    if mode == "ui_error":
                        progress._render = MagicMock(side_effect=RuntimeError("UI failed"))
                    elif mode == "observer_error":
                        progress = MagicMock(side_effect=RuntimeError("observer failed"))
                    result, current_configs, current_calls = self.run_fake(root / mode, progress)
                    self.assertEqual(result, baseline)
                    self.assertEqual(current_configs, configs)
                    self.assertEqual(current_calls, calls, "UI must not add database operations")
                    for cell in self.plan["schedule"]:
                        def read(folder):
                            return json.loads((root / folder / (cell["id"] + ".json")).read_text(encoding="utf-8"))
                        before, after = read("off"), read(mode)
                        for key in ("queries", "summaries", "index_configuration", "capacity_check"):
                            self.assertEqual(before[key], after[key])
                        self.assertTrue(after["valid_for_comparison"])
                    if mode != "observer_error":
                        self.assertIn("48/48", stream.getvalue())

    def test_failure_reports_real_completed_count_and_preserves_cleanup(self):
        events = []
        stream = Terminal()
        progress = LiveProgress(stream)

        def observe(update):
            events.append(update)
            progress(update)

        with TemporaryDirectory() as temporary:
            run = Path(temporary) / "run"
            with self.assertRaisesRegex(RuntimeError, "measurement failure"):
                self.run_fake(run, observe, fail_at=14)
            journal = json.loads((run / "journal.json").read_text(encoding="utf-8"))
            self.assertEqual(journal["status"], "failed")
            self.assertEqual(len(journal["cells"]), 13)
            self.assertTrue(all(e["state"] == "dropped" for e in journal["entries"]))
        self.assertEqual(events[-1]["status"], "failed")
        self.assertEqual(events[-1]["completed"], 13)
        self.assertIn("13/48", stream.getvalue())

    def test_overbudget_is_displayed_as_infeasible_not_success(self):
        events = []
        with TemporaryDirectory() as temporary:
            result, _, _ = self.run_fake(Path(temporary) / "run", events.append, over_budget=True)
        self.assertEqual(result["status"], "complete_with_infeasible_configurations")
        self.assertEqual(sum(e["status"] == "budget_exceeded" for e in events), 36)
        self.assertEqual(events[-1]["status"], "complete_with_infeasible_configurations")
        self.assertEqual(events[-1]["completed"], 48)

    def test_display_receives_no_mutable_plan_or_journal_objects(self):
        def mutate(update):
            update.clear()
        with TemporaryDirectory() as temporary:
            result, _, _ = self.run_fake(Path(temporary) / "run", mutate)
        self.assertEqual(len(result["cells"]), 48)
        self.assertEqual(result["status"], "complete")


class ProgressCliTests(unittest.TestCase):
    def test_opt_in_default_and_display_initialization_failure_preserve_cli_json(self):
        for flag, fail_display in ((False, False), (True, False), (True, True)):
            with self.subTest(flag=flag, fail_display=fail_display):
                args = ["run", "--plan", "unused.json", "--run-dir", "unused",
                        "--approve-plan-sha256", "approved"]
                if flag:
                    args.append("--live-progress")
                output = io.StringIO()
                with patch("strategy_benchmark.main.read_json", return_value={"plan": "test"}), \
                     patch("strategy_benchmark.main.Database") as database, \
                     patch("strategy_benchmark.main.execute", return_value={"status": "complete"}) as run, \
                     patch("strategy_benchmark.main.LiveProgress", side_effect=RuntimeError("UI init") if fail_display else None) as display, \
                     redirect_stdout(output), redirect_stderr(io.StringIO()):
                    self.assertEqual(main(args), 0)
                database.assert_not_called()
                self.assertEqual(json.loads(output.getvalue()), {"status": "complete"})
                self.assertEqual(display.call_count, int(flag))
                self.assertEqual("progress" in run.call_args.kwargs, flag and not fail_display)


if __name__ == "__main__":
    unittest.main()
