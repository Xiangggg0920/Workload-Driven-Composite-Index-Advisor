"""Transparent *heuristic* cost proxy (NOT actual PostgreSQL I/O or milliseconds)."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Mapping
from .candidates import IndexCandidate
from .parser import WorkloadQuery
from .statistics import TableStats


@dataclass(frozen=True)
class ScoredCandidate:
    index: IndexCandidate
    estimated_bytes: int
    # Per statement: estimated logical scan-work reduction (page-scaled proxy)
    savings_by_query: tuple[float, ...]

    @property
    def independent_benefit(self) -> float:
        return sum(self.savings_by_query)


def estimated_index_bytes(candidate: IndexCandidate, stats: TableStats) -> int:
    # Rough B-tree estimate based on avg_width, tuple TID, tuple overhead, page
    # fragmentation/fill factor. This is a planning proxy, not pg_relation_size.
    key_width = sum(max(1, stats.columns[col].avg_width) for col in candidate.columns)
    bytes_per_entry = key_width + 16
    return max(8192, math.ceil(stats.rows * bytes_per_entry * 1.35 / 8192) * 8192)


def _eq_selectivity(table: TableStats, col: str) -> float:
    stat = table.columns[col]
    n = stat.n_distinct
    distinct = max(1.0, -n * table.rows if n < 0 else n)
    return max(1.0 / max(1.0, table.rows), (1.0 - stat.null_frac) / distinct)


def _prefix_selectivity(index: IndexCandidate, query: WorkloadQuery,
                         table: TableStats) -> tuple[float, int]:
    types: dict[str, str] = {}
    for p in query.predicates:
        if p.table != index.table or p.schema != index.schema:
            continue
        rank = {"range": 0, "join": 1, "equality": 2}
        if rank[p.kind] >= rank.get(types.get(p.column, "range"), -1):
            types[p.column] = p.kind
    selectivity = 1.0
    used = 0
    for col in index.columns:
        kind = types.get(col)
        if kind is None:
            break
        used += 1
        if kind == "equality":
            selectivity *= _eq_selectivity(table, col)
        elif kind == "join":
            # Equijoin parameter selectivity is uncertain without join histograms;
            # a bounded proxy avoids treating it as a literal constant.
            selectivity *= max(0.02, _eq_selectivity(table, col))
        else:
            selectivity *= 0.25  # unknown range endpoints: conservative assumption
            break  # B-tree range generally limits further prefix pruning
    return max(selectivity, 1.0 / max(1.0, table.rows)), used


def score_candidate(index: IndexCandidate, queries: tuple[WorkloadQuery, ...],
                    tables: Mapping[str, TableStats]) -> ScoredCandidate:
    table = tables[index.table]
    size = estimated_index_bytes(index, table)
    # A simple page proxy, conservative enough to penalize low-selectivity scans.
    index_pages = max(1.0, size / 8192.0)
    benefits = []
    table_names = sorted(tables)
    for query in queries:
        # Keep one coverage dimension per (query, table). Indexes on separate
        # tables can contribute additively; competing indexes on the same
        # table contribute at most their best value.
        for other_table in table_names:
            if other_table != index.table:
                benefits.append(0.0)
                continue
            selectivity, used = _prefix_selectivity(index, query, table)
            if used == 0:
                benefits.append(0.0)
                continue
            # Logical filtering score scaled by heap pages. We intentionally avoid
            # claiming that PostgreSQL will physically avoid this many heap reads:
            # non-covering B-trees can still touch nearly every heap page, and the
            # planner may prefer SeqScan. Week 3 must measure real BUFFERS.
            heap_pages = table.heap_pages
            index_work = max(1.0, index_pages * selectivity + 2.0)
            proxy_saving = max(0.0, heap_pages * (1.0 - selectivity) - index_work)
            benefits.append(query.weight * proxy_saving)
    return ScoredCandidate(index, size, tuple(benefits))


def score_candidates(candidates: list[IndexCandidate], queries: tuple[WorkloadQuery, ...],
                     tables: Mapping[str, TableStats]) -> list[ScoredCandidate]:
    return [score_candidate(c, queries, tables) for c in candidates]
