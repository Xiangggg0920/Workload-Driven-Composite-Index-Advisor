"""Storage-budgeted index selection with workload overlap accounting."""
from __future__ import annotations
from dataclasses import dataclass
from .cost_model import ScoredCandidate


@dataclass(frozen=True)
class Selection:
    selected: tuple[ScoredCandidate, ...]
    budget_bytes: int
    estimated_benefit: float
    exact: bool

    @property
    def used_bytes(self) -> int:
        return sum(item.estimated_bytes for item in self.selected)


def _gain(item: ScoredCandidate, coverage: tuple[float, ...]) -> float:
    return sum(max(0.0, x - old) for x, old in zip(item.savings_by_query, coverage))


def select_indexes(items: list[ScoredCandidate], budget_bytes: int,
                   exact_limit: int = 16) -> Selection:
    """Maximize weighted sum of best-index-per-query benefit within byte budget.

    Exact exhaustive subset search for <=16 candidates (knapsack-like with
    nonadditive values), otherwise deterministic marginal-benefit greedy. This
    *avoids* double-counting indexes serving the same queries.
    """
    if budget_bytes < 0:
        raise ValueError("budget_bytes must not be negative")
    feasible = sorted((x for x in items if x.estimated_bytes <= budget_bytes and x.independent_benefit > 0),
                      key=lambda c: c.index.label)
    if not feasible:
        return Selection((), budget_bytes, 0.0, True)
    nqueries = len(feasible[0].savings_by_query)
    if any(len(x.savings_by_query) != nqueries for x in feasible):
        raise ValueError("candidate score vectors must be aligned")
    zero = tuple(0.0 for _ in range(nqueries))

    if len(feasible) <= exact_limit:
        best_score = -1.0
        best: tuple[ScoredCandidate, ...] = ()
        def dfs(pos: int, selected: tuple[ScoredCandidate, ...], used: int, covered: tuple[float, ...]):
            nonlocal best, best_score
            if pos == len(feasible):
                value = sum(covered)
                if value > best_score + 1e-9 or (abs(value - best_score) <= 1e-9 and used < sum(x.estimated_bytes for x in best)):
                    best_score, best = value, selected
                return
            item = feasible[pos]
            dfs(pos + 1, selected, used, covered)
            if used + item.estimated_bytes <= budget_bytes:
                next_covered = tuple(max(a, b) for a, b in zip(covered, item.savings_by_query))
                dfs(pos + 1, selected + (item,), used + item.estimated_bytes, next_covered)
        dfs(0, (), 0, zero)
        return Selection(best, budget_bytes, max(0.0, best_score), True)

    # For larger candidate sets, use a bounded, reproducible heuristic.
    chosen: list[ScoredCandidate] = []
    unused = feasible[:]
    covered = zero
    remaining = budget_bytes
    while True:
        choices = [( _gain(x, covered) / x.estimated_bytes, _gain(x, covered), x)
                   for x in unused if x.estimated_bytes <= remaining]
        if not choices:
            break
        choices.sort(key=lambda part: (-part[0], -part[1], part[2].index.label))
        _, improvement, pick = choices[0]
        if improvement <= 1e-9:
            break
        chosen.append(pick)
        unused.remove(pick)
        remaining -= pick.estimated_bytes
        covered = tuple(max(a, b) for a, b in zip(covered, pick.savings_by_query))
    return Selection(tuple(chosen), budget_bytes, sum(covered), False)
