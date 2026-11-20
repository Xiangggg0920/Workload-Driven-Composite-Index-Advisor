"""One approved real index build followed by journal-based recovery/cleanup."""
from pathlib import Path
import json

from dotenv import load_dotenv

from benchmark.runner import timestamp
from dataset.prepare_sf1 import ROOT
from strategy_benchmark.database import Database, verify_environment
from strategy_benchmark.engine import Journal, recovery, save_new
from strategy_benchmark.plan import MIB, asset_hashes, validate_plan


APPROVED = "a8024363ffca87990ef8536653a2641a9264cc7a49ea1ae0990b28bc3310a8cd"


def main():
    load_dotenv(ROOT / ".env")
    plan = json.loads((ROOT / "benchmark/results/3c-review-v2/plan.json").read_text(encoding="utf-8"))
    source = (ROOT / "workload/benchmark20.sql").read_bytes().decode("utf-8-sig")
    validate_plan(plan, source)
    if plan["plan_sha256"] != APPROVED or asset_hashes() != plan["asset_hashes"]:
        raise RuntimeError("Approved plan/assets mismatch; STOP")
    directory = ROOT / "benchmark/results/3c-integration-e4b8de6111b3"
    directory.mkdir(exist_ok=False)
    save_new(directory / "plan.json", plan)
    with (directory / "workload.sql").open("x", encoding="utf-8", newline="") as stream:
        stream.write(source)
    # Use exactly one already-approved small orders index; no new index design.
    spec = next(s for c in plan["schedule"] for s in c["indexes"]
                if s["table"] == "orders" and s["columns"] == ["o_orderdate"])
    journal = Journal(directory, {"run_id": plan["run_id"], "plan_sha256": APPROVED,
        "database": plan["database"], "ownership_tag": plan["ownership_tag"],
        "status": "integration_starting", "entries": [], "cells": []})
    journal.flush()
    report = {"started_at": timestamp(), "plan_sha256": APPROVED, "spec": spec,
              "test": "one real build; persisted intent; recovery preview; recovery execution"}
    db = Database(allow_write=True)
    locked = False
    try:
        verify_environment(plan, db.capture())
        report["database"] = db.identity
        report["indexes_before"] = db.indexes()
        db.acquire()
        locked = True
        entry = {"spec": spec, "oid": None, "state": "pending"}
        journal.data["entries"].append(entry)
        journal.data["status"] = "integration_building"
        journal.flush()
        built = db.build([spec], 100 * MIB, plan["ownership_tag"])
        report["built_indexes"] = built
        assert len(built) == 1 and 0 < built[0]["main_bytes"] <= 100 * MIB
        entry.update(oid=built[0]["oid"], definition=built[0]["definition"],
                     table_oid=built[0]["table_oid"], state="committed")
        journal.data["status"] = "integration_recovery_required"
        journal.flush()
        db.release()
        locked = False
        report["recovery_preview"] = recovery(plan, journal, db)
        assert report["recovery_preview"]["eligible_owned_indexes"] == [spec["name"]]
        report["recovery_execution"] = recovery(plan, journal, db, execute_cleanup=True)
        report["indexes_after"] = db.indexes()
        verify_environment(plan, db.capture())
        assert report["indexes_after"] == report["indexes_before"]
        report["status"] = "passed_no_residual_indexes"
    except BaseException as exc:
        report.update(status="failed_stop", error=type(exc).__name__ + ": " + str(exc))
        # Only the exact journaled index can be recovered; an unsafe cleanup raises.
        try:
            if locked:
                db.release()
                locked = False
            report["failure_recovery"] = recovery(plan, journal, db, execute_cleanup=True)
            report["indexes_after"] = db.indexes()
        except BaseException as cleanup:
            report["cleanup_error"] = type(cleanup).__name__ + ": " + str(cleanup)
        raise
    finally:
        if locked:
            db.release()
        db.close()
        report["finished_at"] = timestamp()
        save_new(directory / "integration.json", report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
