"""Generate equality-first composite index candidates per table/workload query."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .parser import WorkloadQuery
from .statistics import TableStats


@dataclass(frozen=True)
class IndexCandidate:
    schema: str
    table: str
    columns: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"{self.schema}.{self.table}({', '.join(self.columns)})"


def _distinct(stats: TableStats, col: str) -> float:
    n = stats.columns[col].n_distinct
    return max(1.0, -n * stats.rows if n < 0 else n)


def make_candidates(queries: tuple[WorkloadQuery, ...], tables: Mapping[str, TableStats],
                    max_columns: int = 3, max_candidates: int | None = None) -> list[IndexCandidate]:
    """Combine relevant equality and range columns; candidate ordering is heuristic.

    For each table in each query, equality/join columns come first (most distinct
    first), then the most selective range. Prefix candidates of length 2..K are
    emitted. This does NOT claim to find the true optimal PostgreSQL index order.
    """
    counts: dict[IndexCandidate, float] = {}
    for query in queries:
        per_table: dict[str, dict[str, str]] = {}
        for p in query.predicates:
            if p.table not in tables or p.column not in tables[p.table].columns:
                continue
            kinds = per_table.setdefault(p.table, {})
            rank = {"range": 0, "join": 1, "equality": 2}
            if rank[p.kind] > (rank[kinds[p.column]] if p.column in kinds else -1):
                kinds[p.column] = p.kind
        for table, kinds in per_table.items():
            stats = tables[table]
            eq = sorted((c for c, k in kinds.items() if k in ("equality", "join")),
                        key=lambda c: (-_distinct(stats, c), c))
            ranges = sorted((c for c, k in kinds.items() if k == "range"),
                            key=lambda c: (-_distinct(stats, c), c))
            ordered = eq + ranges[:1]
            for end in range(2, min(max_columns, len(ordered)) + 1):
                candidate = IndexCandidate(stats.schema, table, tuple(ordered[:end]))
                counts[candidate] = counts.get(candidate, 0.0) + query.weight
    ranked = sorted(counts, key=lambda c: (-counts[c], c.label))
    # The CLI intentionally calls with max_candidates=None: do not discard a
    # low-frequency but budget-feasible index before its size is estimated.
    return ranked if max_candidates is None else ranked[:max_candidates]
