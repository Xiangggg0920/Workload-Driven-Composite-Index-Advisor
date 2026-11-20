"""Summarize immutable 3C artifacts and render Proposal Exp 1--3 figures.

No database connection or index DDL. Round is the replication unit; the five
measurements inside a cell are averaged before comparing matched baselines.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

from strategy_benchmark.plan import seal


STRATEGIES = ("baseline", "single", "suboptimal", "advisor")
LABELS = {"baseline": "Baseline", "single": "Single-column",
          "suboptimal": "Suboptimal (source order)", "advisor": "Advisor"}
COLORS = {"baseline": "#7c8594", "single": "#337ab7", "suboptimal": "#df9333", "advisor": "#26947d"}
SUBSETS = {"full20": set(range(1, 21)), "advisor16": set(range(1, 17))}
METRICS = ("execution_time_ms", "planning_time_ms", "shared_hit_blocks", "shared_read_blocks")


def mean(values):
    return statistics.fmean(values) if values else None


def geometric_mean(values):
    if not values or any(x <= 0 for x in values):
        return None
    return math.exp(statistics.fmean(math.log(x) for x in values))


def write_csv(path, records):
    if not records:
        return
    fields = list(dict.fromkeys(k for record in records for k in record))
    with Path(path).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def dump(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def collect(directory):
    directory = Path(directory)
    plan = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
    if seal(plan) != plan["plan_sha256"]:
        raise ValueError("Plan hash mismatch; stop analysis")
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    if summary["plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("Summary/plan hash mismatch")
    cells, queries, attempts, capacities, failures, issues, inputs = [], [], [], [], [], [], {}
    for name in ("plan.json", "summary.json", "journal.json", "workload.sql"):
        inputs[name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
    summaries = {c["id"]: c for c in summary["cells"]}
    for cell in plan["schedule"]:
        cid = cell["id"]
        base = {k: cell[k] for k in ("id", "round", "budget_mib", "strategy")}
        result = summaries.get(cid)
        if result is None:
            issues.append(cid + ": missing cell summary")
            cells.append({**base, "status": "missing", "actual_mib": None})
            continue
        path = directory / (cid + ".json")
        inputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        raw = json.loads(path.read_text(encoding="utf-8"))
        row = {**base, "status": result["status"],
               "estimated_mib": result["estimated_added_bytes"] / 2**20,
               "actual_mib": None, "partial_attempted_mib": None}
        if result["status"] != "ok":
            row["partial_attempted_mib"] = result.get("measured_partial_bytes", 0) / 2**20
            failures.append({**base, "status": result["status"],
                "partial_attempted_mib": row["partial_attempted_mib"],
                "note": "No latency substituted; attempted index sizes may be a partial configuration."})
            for i in result.get("measured_attempted_indexes", []):
                capacities.append({**base, "configuration_complete": False,
                    "index_name": i["name"], "definition": i["definition"],
                    "actual_bytes": i["main_bytes"], "total_bytes": i["total_bytes"], "rolled_back": True})
            cells.append(row)
            continue
        if raw.get("plan_sha256") != plan["plan_sha256"] or not raw.get("valid_for_comparison"):
            issues.append(cid + ": invalid measurement metadata")
        if len(raw["queries"]) != 20 or {q["number"] for q in raw["queries"]} != set(range(1, 21)):
            issues.append(cid + ": full20 query identity coverage failed")
        row["actual_mib"] = raw["actual_added_index_bytes_after"] / 2**20
        if row["actual_mib"] > cell["budget_mib"]:
            issues.append(cid + ": actual storage exceeds cap")
        allowed = {i["name"] for i in raw["index_configuration"]}
        for i in raw["index_configuration"]:
            capacities.append({**base, "configuration_complete": True,
                "index_name": i["name"], "definition": i["definition"],
                "estimated_bytes": i.get("estimated_bytes"), "actual_bytes": i["main_bytes"],
                "total_bytes": i["total_bytes"], "rolled_back": False})
        for q in raw["queries"]:
            qrow = {**base, "query": q["number"], "advisor_supported": q["number"] <= 16,
                    "sql_sha256": q["sql_sha256"], "status": q["status"]}
            expected = (("warmup_runs", plan["measurement"]["warmup"]),
                        ("measurements", plan["measurement"]["repeats"]))
            for phase, count in expected:
                if len(q[phase]) != count or any(r["status"] != "ok" for r in q[phase]):
                    issues.append(f"{cid}/Q{q['number']:02d}: incomplete {phase}")
                for r in q[phase]:
                    used = [i["name"] for i in r.get("used_indexes", [])]
                    if not set(used) <= allowed:
                        issues.append(cid + ": unexpected used index")
                    attempt = {**base, "query": q["number"], "phase": r["phase"],
                        "iteration": r["iteration"], "status": r["status"],
                        "started_at": r["started_at"], "used_indexes": "|".join(used),
                        "source_json": path.name}
                    attempt.update({m: r.get(m) for m in METRICS})
                    root = r.get("query_plan", [{}])[0].get("Plan", {})
                    attempt["temp_read_blocks"] = root.get("Temp Read Blocks", 0) if r["status"] == "ok" else None
                    attempt["temp_written_blocks"] = root.get("Temp Written Blocks", 0) if r["status"] == "ok" else None
                    attempts.append(attempt)
            qrow.update({m: q["summary"].get(m, {}).get("mean") for m in METRICS})
            qrow["used_indexes"] = "|".join(sorted({i["name"] for r in q["measurements"] for i in r.get("used_indexes", [])}))
            for label, key in (("temp_read_blocks", "Temp Read Blocks"), ("temp_written_blocks", "Temp Written Blocks")):
                qrow[label] = mean([r["query_plan"][0]["Plan"].get(key, 0) for r in q["measurements"] if r["status"] == "ok"])
            queries.append(qrow)
        for subset in SUBSETS:
            for metric, field in (("execution_ms", "sum_query_mean_execution_ms"),
                                  ("hits", "sum_query_mean_shared_hit_blocks"),
                                  ("reads", "sum_query_mean_shared_read_blocks")):
                row[subset + "_" + metric] = raw["summaries"][subset][field]
            for metric in ("temp_read_blocks", "temp_written_blocks"):
                row[subset + "_" + metric] = sum(q[metric] for q in queries if q["id"] == cid and q["query"] in SUBSETS[subset])
        cells.append(row)
    return plan, summary, cells, queries, attempts, capacities, failures, issues, inputs


def aggregate(cells):
    baselines = {(c["round"], c["budget_mib"]): c for c in cells if c["strategy"] == "baseline" and c["status"] == "ok"}
    result = []
    for budget in (100, 500, 1024):
        for strategy in STRATEGIES:
            group = [c for c in cells if c["budget_mib"] == budget and c["strategy"] == strategy]
            good = [c for c in group if c["status"] == "ok"]
            row = {"budget_mib": budget, "strategy": strategy, "successful_rounds": len(good),
                   "expected_rounds": len(group), "actual_mib": mean([c["actual_mib"] for c in good]),
                   "estimated_mib": next((c.get("estimated_mib") for c in group), None)}
            for subset in SUBSETS:
                times = [c[subset + "_execution_ms"] for c in good]
                ratios = [baselines[(c["round"], budget)][subset + "_execution_ms"] / c[subset + "_execution_ms"]
                          for c in good if (c["round"], budget) in baselines]
                savings_ms = [baselines[(c["round"], budget)][subset + "_execution_ms"] - c[subset + "_execution_ms"]
                              for c in good if (c["round"], budget) in baselines]
                savings_pct = [100 * (1 - 1 / ratio) for ratio in ratios]
                row.update({subset + "_mean_ms": mean(times),
                    subset + "_stdev_ms": statistics.stdev(times) if len(times) > 1 else None,
                    subset + "_min_ms": min(times) if times else None,
                    subset + "_max_ms": max(times) if times else None,
                    subset + "_paired_speedup": geometric_mean(ratios),
                    subset + "_paired_n": len(ratios),
                    subset + "_speedup_min": min(ratios) if ratios else None,
                    subset + "_speedup_max": max(ratios) if ratios else None,
                    subset + "_mean_savings_ms": mean(savings_ms),
                    subset + "_mean_savings_pct": mean(savings_pct),
                    subset + "_mean_hits": mean([c[subset + "_hits"] for c in good]),
                    subset + "_mean_reads": mean([c[subset + "_reads"] for c in good])})
                for metric in ("temp_read_blocks", "temp_written_blocks"):
                    row[subset + "_mean_" + metric] = mean([c.get(subset + "_" + metric, 0) for c in good])
            result.append(row)
    return result


def plot(output, groups, cells, queries, *, measurement):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import TwoSlopeNorm

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "pdf.fonttype": 42})
    by_key = {(g["budget_mib"], g["strategy"]): g for g in groups}
    rounds = len({c["round"] for c in cells if c["status"] == "ok"})
    round_label = "Single round" if rounds == 1 else f"{rounds} rounds"
    measurement_note = (f"Warm cache; {measurement['warmup']} warmups + "
                        f"{measurement['repeats']} measurements per query/cell.")
    total_note = ("Sum of per-query measurement means." if rounds == 1 else
                  "Mean across round totals (sums of per-query measurement means).")
    uncertainty = ("No between-round uncertainty estimate." if rounds == 1 else
                   "Whiskers = min-max of matched round speedups, not confidence intervals.")

    def save(fig, name):
        fig.savefig(output / (name + ".png"), dpi=180, bbox_inches="tight")
        fig.savefig(output / (name + ".svg"), bbox_inches="tight")
        fig.savefig(output / (name + ".pdf"), bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.7))
    for ax, subset in zip(axes, SUBSETS):
        for si, strategy in enumerate(STRATEGIES):
            xx = np.arange(3) + (si - 1.5) * .19
            rows = [by_key[(b, strategy)] for b in (100, 500, 1024)]
            vals = [r[subset + "_paired_speedup"] for r in rows]
            ax.bar(xx, [v if v is not None else np.nan for v in vals], .18,
                   color=COLORS[strategy], label=LABELS[strategy])
            for x, r, v in zip(xx, rows, vals):
                if v is None:
                    ax.text(x, .07, "N/A", rotation=90, ha="center", va="bottom")
                else:
                    lo, hi = r[subset + "_speedup_min"], r[subset + "_speedup_max"]
                    if r[subset + "_paired_n"] > 1:
                        ax.errorbar(x, v, yerr=[[max(0, v-lo)], [max(0, hi-v)]], color="#303846", capsize=2, lw=1)
                    ax.text(x, hi + .04, f"{v:.2f}", ha="center", fontsize=8)
        ax.axhline(1, color="#64748b", lw=.7, linestyle="--")
        ax.set(xticks=range(3), xticklabels=["100", "500", "1024"], xlabel="Budget (MiB)",
               ylabel="Paired speedup vs Baseline (higher is better)", title="Full 20 queries" if subset == "full20" else "Advisor-supported Q01-Q16")
        ax.grid(axis="y", alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle("Exp 1 | Equal-weight workload latency comparison | " + round_label)
    fig.text(.5, .015, "Matched Baseline speedups. " + uncertainty + "\n" + measurement_note,
             ha="center", va="bottom", fontsize=9)
    fig.tight_layout(rect=(0, .1, 1, .95))
    save(fig, "exp1_performance")

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for row_index, subset in enumerate(SUBSETS):
        for col_index, metric in enumerate(("reads", "hits")):
            ax = axes[row_index, col_index]
            for si, strategy in enumerate(STRATEGIES):
                vals = [by_key[(b, strategy)][subset + "_mean_" + metric] for b in (100, 500, 1024)]
                ax.bar(np.arange(3)+(si-1.5)*.19, [v if v is not None else np.nan for v in vals], .18,
                       color=COLORS[strategy], label=LABELS[strategy])
            ax.set(xticks=range(3), xticklabels=["100", "500", "1024"], xlabel="Budget (MiB)",
                   ylabel="Blocks per workload", title=("Full20" if subset == "full20" else "Q01-Q16") + " | shared " + metric)
            ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
            ax.grid(axis="y", alpha=.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .95),
               ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Exp 2 | PostgreSQL execution buffer activity | " + round_label)
    fig.text(.5, .015, total_note + " " + measurement_note + "\n"
             "Root counters include children. Shared reads may hit OS cache; these are not physical disk reads.",
             ha="center", va="bottom", fontsize=9)
    fig.tight_layout(rect=(0, .09, 1, .95))
    save(fig, "exp2_buffers")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    markers = {100: "o", 500: "s", 1024: "^"}
    for ax, subset in zip(axes, SUBSETS):
        for strategy in STRATEGIES:
            for budget in (100, 500, 1024):
                if strategy == "baseline" and budget != 100:
                    continue  # Baseline always saves exactly zero at zero added bytes.
                r = by_key[(budget, strategy)]
                x, y = r["actual_mib"], r[subset + "_mean_savings_ms"]
                if x is None or y is None:
                    continue
                ax.scatter(x, y/1000, color=COLORS[strategy], marker=markers[budget], s=65,
                           label=LABELS[strategy] if budget == 100 else None,
                           edgecolors="white", linewidths=.5, zorder=3)
                dx, dy, align = {"baseline": (8, 16, "left"), "single": (-8, -16, "right"),
                    "suboptimal": (-10, 12, "right"), "advisor": (10, -16, "left")}[strategy]
                if budget == 100 and strategy == "suboptimal":
                    dx, dy, align = 10, -18, "left"
                elif budget == 100 and strategy == "advisor":
                    dx, dy, align = 40, 0, "left"
                ax.annotate("Baseline" if strategy == "baseline" else str(budget), (x, y/1000),
                    xytext=(dx, dy), textcoords="offset points", ha=align, fontsize=8,
                    color=COLORS[strategy],
                    arrowprops={"arrowstyle": "-", "color": COLORS[strategy], "lw": .6})
        ax.axhline(0, color="#64748b", lw=.7)
        ax.set(xlabel="Actual added index main-fork size (MiB)", ylabel="Workload time saved vs paired Baseline (seconds)",
               title="Full 20 queries" if subset == "full20" else "Advisor-supported Q01-Q16")
        baseline_values = []
        for budget in (100, 500, 1024):
            ms = by_key[(budget, "baseline")][subset + "_mean_ms"]
            baseline_values.append(f"{budget}: {ms/1000:.3f}" if ms is not None else f"{budget}: N/A")
        baseline_stat = "Baseline workload" if rounds == 1 else "Mean Baseline workload"
        ax.set_title(ax.get_title() + "\n" + baseline_stat + " (s) by budget (MiB):\n"
                     + " | ".join(baseline_values), fontsize=10)
        ax.grid(alpha=.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .94),
               ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Exp 3 | Storage versus paired workload savings | " + round_label)
    fig.text(.5, .015, "Each point uses its own budget's paired Baseline. Baseline drift limits cross-budget comparisons.\n"
             "Descriptive observations only; no Pareto frontier inferred. Labels = nominal budget; x = pg_relation_size.\n"
             + total_note + " " + measurement_note, ha="center", va="bottom", fontsize=8)
    fig.tight_layout(rect=(0, .15, 1, .93))
    save(fig, "exp3_storage_tradeoff")

    baseline = {(q["round"], q["budget_mib"], q["query"]): q["execution_time_ms"]
                for q in queries if q["strategy"] == "baseline"}
    matrix, names = [], []
    for budget in (100, 500, 1024):
        for strategy in STRATEGIES[1:]:
            ratios = []
            for qid in range(1, 21):
                qs = [q for q in queries if q["budget_mib"] == budget and q["strategy"] == strategy and q["query"] == qid]
                ratio = geometric_mean([baseline[(q["round"], budget, qid)] / q["execution_time_ms"] for q in qs
                                        if (q["round"], budget, qid) in baseline])
                ratios.append(math.log2(ratio) if ratio else np.nan)
            matrix.append(ratios)
            names.append(f"{budget} MiB / {LABELS[strategy]}")
    values = np.array(matrix)
    finite = np.abs(values[np.isfinite(values)])
    limit = max(1, float(finite.max())) if len(finite) else 1
    fig, ax = plt.subplots(figsize=(16, 5))
    im = ax.imshow(values, aspect="auto", cmap="RdYlGn", norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit))
    for ri, line in enumerate(matrix):
        for ci, val in enumerate(line):
            ax.text(ci, ri, f"{2**val:.2g}" if math.isfinite(val) else "N/A", fontsize=7, ha="center", va="center")
    query_stat = "Baseline / strategy" if rounds == 1 else "Geometric mean of round-paired Baseline / strategy ratios"
    ax.set(yticks=range(len(names)), yticklabels=names, xticks=range(20), xticklabels=[f"Q{i:02d}" for i in range(1,21)],
           title="Exp 1 detail | Per-query speedup | " + round_label)
    ax.axvline(15.5, color="#111827", linestyle="--", lw=1.5)
    fig.colorbar(im, ax=ax, label="log2(speedup)")
    fig.text(.5, .015, "Cell numbers = " + query_stat + "; colors = log2(speedup); values > 1 are faster.\n"
             + measurement_note + " Q17-Q20 are not parsed by Advisor.",
             ha="center", va="bottom", fontsize=9)
    fig.tight_layout(rect=(0, .11, 1, 1))
    save(fig, "exp1_per_query")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--interrupted-run-dir", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    values = collect(args.run_dir)
    plan, summary, cells, queries, attempts, capacities, failures, issues, inputs = values
    groups = aggregate(cells)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    interrupted, interrupted_cells = [], []
    for run_dir in args.interrupted_run_dir:
        old = json.loads((run_dir / "journal.json").read_text(encoding="utf-8"))
        if old["plan_sha256"] != plan["plan_sha256"]:
            raise ValueError("Interrupted run plan hash mismatch; stop")
        completed = {c["id"] for c in old["cells"]}
        interrupted.append({"run_dir": str(run_dir), "status": old["status"], "error": old.get("error"),
            "completed_cells": len(completed), "not_completed_cells": [c["id"] for c in plan["schedule"] if c["id"] not in completed],
            "included_in_primary_comparison": False,
            "reason": "Interrupted controller run retained separately; primary comparison uses an entire balanced rerun of the identical approved plan.",
            "journal_sha256": hashlib.sha256((run_dir / "journal.json").read_bytes()).hexdigest()})
        for c in old["cells"]:
            record = {"run_dir": str(run_dir), **{k: c[k] for k in ("id", "round", "budget_mib", "strategy", "status")},
                      "actual_mib": c.get("actual_added_bytes", 0) / 2**20}
            for subset in SUBSETS:
                record[subset + "_execution_ms"] = c.get("summaries", {}).get(subset, {}).get("sum_query_mean_execution_ms")
            interrupted_cells.append(record)
    if interrupted:
        dump(args.output_dir / "interrupted_runs.json", interrupted)
        write_csv(args.output_dir / "interrupted_cells.csv", interrupted_cells)
    for name, data in (("cells", cells), ("queries", queries), ("attempts", attempts),
                       ("index_capacities", capacities), ("aggregates", groups), ("infeasible", failures)):
        write_csv(args.output_dir / (name + ".csv"), data)
    report = {"plan_sha256": plan["plan_sha256"], "run_status": summary["status"],
        "expected_cells": len(plan["schedule"]), "successful_cells": sum(c["status"] == "ok" for c in cells),
        "infeasible_cells": len(failures), "successful_measurements": sum(a["status"] == "ok" and a["phase"] == "measurement" for a in attempts),
        "successful_warmups": sum(a["status"] == "ok" and a["phase"] == "warmup" for a in attempts),
        "artifact_issues": issues, "aggregates": groups, "missing_or_infeasible": failures,
        "interrupted_runs": interrupted,
        "method": {"replication_unit": "round; five query measurements averaged within each cell",
            "workload_latency": "sum of per-query mean execution time; excludes planning, builds and preconditioning",
            "speedup": "geometric mean of baseline/current ratios paired on round and budget",
            "buffers": "sum of per-query mean root shared counters; child counters are inclusive and not added",
            "io_limit": "warm-cache shared reads are not direct physical disk I/O measurements",
            "storage": "actual pg_relation_size main fork; infeasible partial builds are not full configuration sizes",
            "uncertainty": "One round: no between-round variance estimate; five measurements are within-cell repeats."
                if plan["rounds"] == 1 else "Sample standard deviation and min-max across available rounds, not independent query replicates."},
        "input_sha256": inputs}
    dump(args.output_dir / "analysis.json", report)
    if issues:
        raise ValueError("Artifact validation issues; see analysis.json; plots withheld")
    plot(args.output_dir, groups, cells, queries, measurement=plan["measurement"])
    print(json.dumps({k: report[k] for k in ("run_status", "expected_cells", "successful_cells", "infeasible_cells", "successful_measurements", "successful_warmups", "artifact_issues")}))


if __name__ == "__main__":
    main()
