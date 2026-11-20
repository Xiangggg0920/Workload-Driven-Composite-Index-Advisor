"""Approval-gated orchestration and durable ownership journal."""
from __future__ import annotations

import json
from pathlib import Path

from benchmark.runner import BenchmarkConfig, new_report, run_benchmark, timestamp
from benchmark.sql import split_workload
from .database import Database, SafetyError, OverBudget, owned, verify_environment
from .plan import MIB, asset_hashes, validate_plan
from .artifacts import save_json_new as save_new, replace_json


class Journal:
    def __init__(self, directory, data):
        self.path = Path(directory) / "journal.json"
        self.data = data

    def flush(self):
        replace_json(self.path, self.data)


def validate_journal(plan, journal):
    expected = {s["name"]: s for cell in plan["schedule"] for s in cell["indexes"]}
    if (journal["plan_sha256"] != plan["plan_sha256"] or journal["run_id"] != plan["run_id"]
            or journal["ownership_tag"] != plan["ownership_tag"] or journal["database"] != plan["database"]):
        raise SafetyError("Journal/plan identity mismatch")
    seen = set()
    for entry in journal["entries"]:
        name = entry["spec"]["name"]
        if name in seen or expected.get(name) != entry["spec"]:
            raise SafetyError("Journal contains unapproved/duplicate index specifications")
        if entry["state"] not in {"pending", "committed", "rolled_back", "dropped", "cleanup_failed"}:
            raise SafetyError("Unknown journal state")
        seen.add(name)


def used_indexes(node):
    result = {node["Index Name"]} if "Index Name" in node else set()
    for child in node.get("Plans", []):
        result.update(used_indexes(child))
    return result


def annotate(raw, cell, actual, supported):
    by_name = {index["name"]: index for index in actual}
    for query, original_number in zip(raw["queries"], cell["query_order"]):
        query["execution_position"] = query["number"]
        query["number"] = original_number
        query["advisor_supported"] = original_number in supported
        for run in query["warmup_runs"] + query["measurements"]:
            names = sorted(used_indexes(run["query_plan"][0]["Plan"])) if run["status"] == "ok" else []
            if not set(names) <= set(by_name):
                raise SafetyError("A plan used an unexpected index")
            run["used_indexes"] = [{"name": name, "oid": by_name[name]["oid"],
                                     "definition": by_name[name]["definition"]} for name in names]
    raw["strategy"] = cell["strategy"]
    raw["budget_mib"] = cell["budget_mib"]
    raw["round"] = cell["round"]
    raw["index_configuration"] = actual
    raw["actual_added_index_bytes"] = sum(i["main_bytes"] for i in actual if i.get("managed_this_cell"))
    raw["summaries"] = {}
    for label, numbers in (("full20", set(range(1, 21))), ("advisor16", set(supported))):
        queries = [q for q in raw["queries"] if q["number"] in numbers]
        complete = len(queries) == len(numbers) and all(q["status"] == "ok" for q in queries)
        raw["summaries"][label] = {"query_count": len(queries), "complete": complete,
            "sum_query_mean_execution_ms": sum(q["summary"]["execution_time_ms"]["mean"] for q in queries) if complete else None,
            "sum_query_mean_shared_hit_blocks": sum(q["summary"]["shared_hit_blocks"]["mean"] for q in queries) if complete else None,
            "sum_query_mean_shared_read_blocks": sum(q["summary"]["shared_read_blocks"]["mean"] for q in queries) if complete else None}
    return raw


def clean(db, plan, journal):
    validate_journal(plan, journal.data)
    dropped = db.cleanup(journal.data["entries"], plan["ownership_tag"])
    for entry in journal.data["entries"]:
        if entry["state"] in {"pending", "committed", "cleanup_failed"}:
            entry["state"] = "dropped"
    journal.flush()
    return dropped


def paired_comparisons(cells):
    baseline = {(c["round"], c["budget_mib"]): c for c in cells
                if c["strategy"] == "baseline" and c["status"] == "ok"}
    result = []
    for cell in cells:
        reference = baseline.get((cell["round"], cell["budget_mib"]))
        record = {k: cell[k] for k in ("id", "round", "budget_mib", "strategy", "status")}
        for label in ("full20", "advisor16"):
            valid = cell["status"] == "ok" and reference is not None
            current = cell.get("summaries", {}).get(label, {}).get("sum_query_mean_execution_ms")
            base = reference["summaries"][label]["sum_query_mean_execution_ms"] if valid else None
            record[label + "_speedup"] = base / current if valid and current else None
        result.append(record)
    return result


def dry_run(plan, source, db):
    validate_plan(plan, source)
    if asset_hashes() != plan["asset_hashes"]:
        raise SafetyError("Implementation assets changed since plan generation")
    environment = db.capture()
    verify_environment(plan, environment)
    return {"status": "dry_run_ok", "created_at": timestamp(), "database": db.identity,
            "plan_sha256": plan["plan_sha256"], "cells": len(plan["schedule"]),
            "planned_create_count": sum(len(c["indexes"]) for c in plan["schedule"]),
            "measurement": plan["measurement"], "rounds": plan["rounds"],
            "indexes_before": environment["indexes"], "indexes_after": db.indexes(),
            "ddl_executed": False, "workload_executed": False, "actual_index_sizes_measured": False}


def execute(plan, source, directory, approval, *, database_factory=Database, runner=run_benchmark, progress=None):
    if approval != plan["plan_sha256"]:
        raise SafetyError("Execution requires the exact reviewed plan SHA256")
    validate_plan(plan, source)
    if asset_hashes() != plan["asset_hashes"]:
        raise SafetyError("Implementation assets changed; review a new plan")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    save_new(directory / "plan.json", plan)
    with (directory / "workload.sql").open("x", encoding="utf-8", newline="") as stream:
        stream.write(source)
    journal = Journal(directory, {"run_id": plan["run_id"], "plan_sha256": plan["plan_sha256"],
        "database": plan["database"], "ownership_tag": plan["ownership_tag"],
        "status": "starting", "entries": [], "cells": [], "data_signature": None})
    journal.flush()
    db = database_factory(allow_write=True)
    reader = None
    locked = False
    current = None

    def report(status):
        nonlocal progress
        if progress is None:
            return
        # Pass only new scalar metadata, never mutable plan/journal objects.
        cell = current or {}
        event = {"status": status, "completed": len(journal.data["cells"]),
                 "total": len(plan["schedule"]), "rounds": plan["rounds"],
                 "round": cell.get("round", "-"), "strategy": cell.get("strategy", "-"),
                 "budget_mib": cell.get("budget_mib", "-")}
        try:
            progress(event)
        except Exception:
            progress = None  # Preserve normal execution/output if an observer fails.

    try:
        report("starting")
        verify_environment(plan, db.capture())
        db.acquire()
        locked = True
        reader = database_factory(allow_write=False)
        if reader.identity != plan["database"] or reader.settings() != plan["environment"]["settings"]:
            raise SafetyError("Measurement connection differs from reviewed environment")
        statements = split_workload(source)
        for cell in plan["schedule"]:
            current = cell
            verify_environment(plan, db.capture())
            entries = [{"spec": s, "oid": None, "state": "pending"} for s in cell["indexes"]]
            journal.data["entries"].extend(entries)
            journal.data["status"] = "building:" + cell["id"]
            journal.flush()  # Durable intent BEFORE CREATE; COMMENT is atomic with CREATE.
            report("building")
            cell_result = {"id": cell["id"], "round": cell["round"], "budget_mib": cell["budget_mib"],
                "strategy": cell["strategy"], "estimated_added_bytes": sum(s["estimated_bytes"] for s in cell["indexes"])}
            try:
                built = db.build(cell["indexes"], cell["budget_mib"] * MIB, plan["ownership_tag"])
            except OverBudget as exc:
                for entry in entries:
                    entry["state"] = "rolled_back"
                cell_result.update(status="budget_exceeded", measured_attempted_indexes=exc.records,
                    measured_partial_bytes=sum(r["main_bytes"] for r in exc.records),
                    performance_measured=False, note="Entire build rolled back; no trimming or backfill")
                journal.data["cells"].append(cell_result)
                journal.flush()
                save_new(directory / (cell["id"] + ".json"), cell_result)
                verify_environment(plan, db.capture())
                report("budget_exceeded")
                continue
            for entry, index in zip(entries, built):
                entry.update(oid=index["oid"], definition=index["definition"], table_oid=index["table_oid"], state="committed")
            journal.data["status"] = "measuring:" + cell["id"]
            journal.flush()
            with db.guard_data():
                if db.statistics_signature() != plan["environment"]["column_statistics_sha256"]:
                    raise SafetyError("Column statistics changed during index build")
                report("prewarming")
                prewarm_started = timestamp()
                signature = db.data_signature()  # Identical full-table warmup/content check for EVERY cell.
                prewarm_finished = timestamp()
                if {table: int(value[0]) for table, value in signature.items()} != plan["expected_rows"]:
                    raise SafetyError("SF1 row counts differ from 3A acceptance")
                if journal.data["data_signature"] is None:
                    journal.data["data_signature"] = signature
                    journal.flush()
                elif signature != journal.data["data_signature"]:
                    raise SafetyError("Data content changed between strategies")
                actual = db.indexes()
                expected_names = {i["name"] for i in plan["environment"]["indexes"]} | {s["name"] for s in cell["indexes"]}
                if {i["name"] for i in actual} != expected_names:
                    raise SafetyError("Unexpected index appeared before measurement")
                expected_specs = {s["name"]: s for s in cell["indexes"]}
                for index in actual:
                    index["managed_this_cell"] = index["name"] in expected_specs
                    index["estimated_bytes"] = expected_specs.get(index["name"], {}).get("estimated_bytes")
                report("measuring")
                raw = new_report(source, "workload/benchmark20.sql", BenchmarkConfig(**plan["measurement"]), cell["id"])
                maintenance_before = db.maintenance()
                try:
                    raw = runner(reader.conn, [statements[n - 1] for n in cell["query_order"]], raw,
                                 BenchmarkConfig(**plan["measurement"]))
                except BaseException as exc:
                    raw.update(status="runner_interrupted", error=type(exc).__name__ + ": " + str(exc))
                    save_new(directory / (cell["id"] + ".runner.json"), raw)
                    raise
                # Save the Runner result even if annotation or validation subsequently fails.
                save_new(directory / (cell["id"] + ".runner.json"), raw)
                raw = annotate(raw, cell, actual, plan["supported_queries"])
                raw["data_signature"] = signature
                raw["query_order"] = cell["query_order"]
                raw["cache_preconditioning"] = {"policy": plan["cache_policy"], "started_at": prewarm_started,
                    "finished_at": prewarm_finished, "table_guard": "SHARE; released before DROP INDEX"}
                raw["plan_sha256"] = plan["plan_sha256"]
                raw["maintenance_before"] = maintenance_before
                raw["maintenance_after"] = db.maintenance()
                raw["column_statistics_sha256"] = db.statistics_signature()
                after = db.indexes()
                raw["indexes_after_measurement"] = after
                raw["actual_added_index_bytes_after"] = sum(i["main_bytes"] for i in after if i["name"] in {s["name"] for s in cell["indexes"]})
                raw["runner_status"] = raw["status"]
                raw["capacity_check"] = {"budget_bytes": cell["budget_mib"] * MIB,
                    "actual_added_index_bytes": raw["actual_added_index_bytes_after"],
                    "passed": raw["actual_added_index_bytes_after"] <= cell["budget_mib"] * MIB}
                raw["valid_for_comparison"] = (raw["runner_status"] == "ok"
                    and all(s["complete"] for s in raw["summaries"].values())
                    and {i["name"] for i in after} == expected_names and raw["capacity_check"]["passed"]
                    and raw["column_statistics_sha256"] == plan["environment"]["column_statistics_sha256"])
                if not raw["valid_for_comparison"]:
                    raw["status"] = "invalid_for_comparison"
                save_new(directory / (cell["id"] + ".json"), raw)
                if not raw["valid_for_comparison"]:
                    raise SafetyError("Measurement incomplete, inventory changed, or actual budget exceeded")
                cell_result.update(status="ok", actual_added_bytes=raw["actual_added_index_bytes_after"],
                                   performance_measured=True, summaries=raw["summaries"])
            report("cleaning")
            clean(db, plan, journal)
            verify_environment(plan, db.capture())
            journal.data["cells"].append(cell_result)
            journal.flush()
            report("cell_ok")
        report("verifying")
        with db.guard_data():
            if db.data_signature() != journal.data["data_signature"]:
                raise SafetyError("Final content signature changed")
        verify_environment(plan, db.capture())
        infeasible = sum(c["status"] == "budget_exceeded" for c in journal.data["cells"])
        journal.data["status"] = "complete_with_infeasible_configurations" if infeasible else "complete"
        journal.data["budget_exceeded_cells"] = infeasible
        journal.data["all_configurations_budget_feasible"] = not infeasible
        journal.data["comparisons"] = paired_comparisons(journal.data["cells"])
    except BaseException as exc:
        journal.data["status"] = "failed"
        journal.data["error"] = type(exc).__name__ + ": " + str(exc)
        journal.flush()
        report("failed")
        raise
    finally:
        try:
            if locked:
                clean(db, plan, journal)
        except BaseException as exc:
            journal.data["status"] = "cleanup_required"
            journal.data["cleanup_error"] = type(exc).__name__ + ": " + str(exc)
            report("cleanup_required")
        finally:
            if reader:
                reader.close()
            try:
                if locked:
                    db.release()
            finally:
                db.close()
                journal.flush()
    save_new(directory / "summary.json", journal.data)
    report(journal.data["status"])
    if journal.data["status"] not in {"complete", "complete_with_infeasible_configurations"}:
        raise SafetyError("Cleanup incomplete; use reviewed recovery procedure")
    return journal.data


def recovery(plan, journal, db, *, execute_cleanup=False):
    validate_journal(plan, journal.data)
    if db.identity != plan["database"]:
        raise SafetyError("Recovery database identity mismatch")
    actual = db.indexes()
    known_names = {e["spec"]["name"] for e in journal.data["entries"]}
    if any(i["comment"] == plan["ownership_tag"] and i["name"] not in known_names for i in actual):
        raise SafetyError("Unjournaled ownership-tagged index; manual review required")
    selected = []
    for entry in journal.data["entries"]:
        if entry["state"] not in {"pending", "committed", "cleanup_failed"}:
            continue
        match = next((i for i in actual if i["name"] == entry["spec"]["name"]), None)
        if match is None and any(i["oid"] == entry.get("oid") for i in actual):
            raise SafetyError("Journaled OID was renamed; manual review required")
        if match is not None and not owned(match, entry, plan["ownership_tag"], db.identity["role"]):
            raise SafetyError("Recovery ownership check failed; no DDL is allowed")
        if match is not None:
            selected.append(match["name"])
    if execute_cleanup:
        db.acquire()
        try:
            clean(db, plan, journal)
            journal.data["status"] = "recovered_clean"
            journal.flush()
        finally:
            db.release()
    return {"eligible_owned_indexes": selected, "ddl_executed": execute_cleanup,
            "status": "recovered_clean" if execute_cleanup else "recovery_dry_run"}
