"""Plan/dry-run are read-only. Run/recover --execute require explicit approval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

from dotenv import load_dotenv

from dataset.prepare_sf1 import ROOT
from .database import Database, verify_environment
from .engine import Journal, dry_run, execute, recovery, save_new
from .plan import build_plan, ddl_manifest, validate_plan, file_hash


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan_command = commands.add_parser("plan", help="read-only planning, write review artifacts locally")
    plan_command.add_argument("--source-3b", type=Path, required=True)
    plan_command.add_argument("--acceptance", type=Path, required=True)
    plan_command.add_argument("--output-dir", type=Path, required=True)
    plan_command.add_argument("--seed", type=int, default=20261120)
    plan_command.add_argument("--warmup", type=int, default=2)
    plan_command.add_argument("--repeats", type=int, default=5)
    plan_command.add_argument("--rounds", type=int, default=1, help="positive round count; default 1 (12 cells)")
    plan_command.add_argument("--statement-timeout-ms", type=int, default=120000)
    plan_command.add_argument("--run-id", default=None)
    inspect_command = commands.add_parser("dry-run", help="validate a reviewed plan without DDL or measurements")
    inspect_command.add_argument("--plan", type=Path, required=True)
    inspect_command.add_argument("--output", type=Path, required=True)
    run_command = commands.add_parser("run", help="ONLY after approval: create/measure/clean managed indexes")
    run_command.add_argument("--plan", type=Path, required=True)
    run_command.add_argument("--run-dir", type=Path, required=True)
    run_command.add_argument("--approve-plan-sha256", required=True)
    recover_command = commands.add_parser("recover", help="default read-only recovery preview")
    recover_command.add_argument("--run-dir", type=Path, required=True)
    recover_command.add_argument("--execute", action="store_true")
    recover_command.add_argument("--approve-run-id")
    args = parser.parse_args(argv)
    load_dotenv(ROOT / ".env")
    source = (ROOT / "workload/benchmark20.sql").read_bytes().decode("utf-8-sig")
    db = None
    try:
        if args.command == "plan":
            if args.output_dir.exists():
                raise ValueError("Output directory exists; never overwrite review artifacts")
            db = Database(allow_write=False)
            environment = db.capture()
            plan = build_plan(source, read_json(args.source_3b), read_json(args.acceptance), environment,
                args.run_id or uuid.uuid4().hex[:12], uuid.uuid4().hex, seed=args.seed,
                warmup=args.warmup, repeats=args.repeats, rounds=args.rounds,
                statement_timeout_ms=args.statement_timeout_ms)
            verify_environment(plan, environment)
            plan["input_hashes"] = {str(args.source_3b): file_hash(args.source_3b), str(args.acceptance): file_hash(args.acceptance)}
            from .plan import seal
            plan["plan_sha256"] = seal(plan)
            args.output_dir.mkdir(parents=True, exist_ok=False)
            save_new(args.output_dir / "plan.json", plan)
            with (args.output_dir / "planned-ddl.sql").open("x", encoding="utf-8") as stream:
                stream.write(ddl_manifest(plan))
            result = {"status": "plan_created_read_only", "plan_sha256": plan["plan_sha256"],
                      "run_id": plan["run_id"], "cells": len(plan["schedule"]),
                      "ddl_executed": False, "measurement": plan["measurement"]}
        elif args.command == "dry-run":
            if args.output.exists():
                raise ValueError("Output already exists")
            plan = read_json(args.plan)
            db = Database(allow_write=False)
            result = dry_run(plan, source, db)
            save_new(args.output, result)
        elif args.command == "run":
            plan = read_json(args.plan)
            result = execute(plan, source, args.run_dir, args.approve_plan_sha256)
        else:
            plan = read_json(args.run_dir / "plan.json")
            saved_source = (args.run_dir / "workload.sql").read_bytes().decode("utf-8-sig")
            validate_plan(plan, saved_source)
            if args.execute and args.approve_run_id != plan["run_id"]:
                raise ValueError("Recovery execution requires the exact approved run id")
            journal = Journal(args.run_dir, read_json(args.run_dir / "journal.json"))
            db = Database(allow_write=args.execute)
            result = recovery(plan, journal, db, execute_cleanup=args.execute)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        print(f"Strategy benchmark stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    raise SystemExit(main())
