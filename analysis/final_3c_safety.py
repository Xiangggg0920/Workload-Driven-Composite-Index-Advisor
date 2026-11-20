"""Read-only closing check after the approved experiment; never runs DDL."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from dotenv import load_dotenv

from benchmark.runner import timestamp
from dataset.prepare_sf1 import ROOT
from dataset.verify_sf1 import smoke_digest
from strategy_benchmark.database import Database, verify_environment
from strategy_benchmark.engine import save_new
from strategy_benchmark.plan import asset_hashes, validate_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Do not overwrite earlier safety evidence")
    load_dotenv(ROOT / ".env")
    plan = json.loads((args.run_dir / "plan.json").read_text(encoding="utf-8"))
    journal = json.loads((args.run_dir / "journal.json").read_text(encoding="utf-8"))
    validate_plan(plan, (ROOT / "workload/benchmark20.sql").read_bytes().decode("utf-8-sig"))
    protected = json.loads((ROOT / "benchmark/results/3c-development-start.json").read_text(encoding="utf-8"))["hashes"]
    protected.update(json.loads((ROOT / "benchmark/results/sf1-3ab-start-state.json").read_text(encoding="utf-8"))["protected_hashes"])
    changed = [name for name, expected in protected.items()
               if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected]
    smoke_before = json.loads((ROOT / "benchmark/results/sf1-3a-smoke-content-before.json").read_text(encoding="utf-8"))["tables"]
    smoke_after = smoke_digest()
    db = Database(allow_write=False)
    try:
        environment = db.capture()
        verify_environment(plan, environment)
        size = db.rows("SELECT pg_database_size(current_database())")[0][0]
    finally:
        db.close()
    report = {"checked_at": timestamp(), "database": environment["identity"],
              "plan_sha256": plan["plan_sha256"], "implementation_assets_unchanged": asset_hashes() == plan["asset_hashes"],
              "protected_files_changed": changed, "indexes_after": environment["indexes"],
              "smoke_content_unchanged": smoke_after == smoke_before,
              "smoke_after": smoke_after, "database_size_bytes": size,
              "disk_free_bytes": shutil.disk_usage(ROOT).free,
              "journal_status": journal["status"],
              "active_journal_entries": [e["spec"]["name"] for e in journal["entries"]
                                         if e["state"] not in ("dropped", "rolled_back")],
              "formal_controller_final_signature_verified": journal["status"] in
                  ("complete", "complete_with_infeasible_configurations"),
              "check_performed_no_ddl": True}
    report["passed"] = (not changed and report["implementation_assets_unchanged"]
        and report["smoke_content_unchanged"] and not report["indexes_after"]
        and not report["active_journal_entries"] and report["formal_controller_final_signature_verified"])
    save_new(args.output, report)
    print(json.dumps(report, ensure_ascii=False))
    if not report["passed"]:
        raise RuntimeError("Final safety check failed; STOP")


if __name__ == "__main__":
    main()
