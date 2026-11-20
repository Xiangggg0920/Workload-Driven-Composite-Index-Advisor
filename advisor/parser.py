"""Conservative SQL workload parser for the benchmark's SELECT/AND predicates.

Deliberately *rejects* unsupported boolean logic instead of generating misleading
index candidates. This is not a general PostgreSQL SQL parser.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping

TOKEN = re.compile(
    r"(?P<SPACE>\s+)|(?P<COMMENT>--[^\n]*|/\*[\s\S]*?\*/)|"
    r"(?P<STRING>'(?:''|[^'])*')|(?P<QUOTED>\"(?:\"\"|[^\"])*\")|"
    r"(?P<NUMBER>\d+(?:\.\d+)?)|(?P<OP><=|>=|<>|!=|=|<|>)|"
    r"(?P<PUNCT>[(),;.*+\-])|(?P<WORD>[A-Za-z_][A-Za-z_0-9$]*)|(?P<OTHER>.)"
)
STOP = {"WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "OFFSET", "FETCH", "UNION", "EXCEPT", "INTERSECT", "FOR"}
OPERATORS = {"=", "<", "<=", ">", ">="}


@dataclass(frozen=True)
class Token:
    kind: str
    text: str

    @property
    def upper(self) -> str:
        return self.text.upper()


@dataclass(frozen=True)
class Predicate:
    schema: str
    table: str
    column: str
    kind: str  # equality, range, join
    operator: str


@dataclass(frozen=True)
class WorkloadQuery:
    number: int
    sql: str
    weight: float
    predicates: tuple[Predicate, ...]


@dataclass(frozen=True)
class ParseResult:
    queries: tuple[WorkloadQuery, ...]
    warnings: tuple[str, ...]


def tokenize(sql: str) -> list[Token]:
    out = []
    for match in TOKEN.finditer(sql):
        kind = match.lastgroup
        if kind not in ("SPACE", "COMMENT"):
            out.append(Token(kind, match.group()))
    return out


def split_statements(source: str) -> list[list[Token]]:
    chunks: list[list[Token]] = []
    current: list[Token] = []
    for token in tokenize(source):
        if token.text == ";":
            if current:
                chunks.append(current)
                current = []
        else:
            current.append(token)
    if current:
        chunks.append(current)
    return chunks


def _name(t: Token) -> str | None:
    if t.kind == "QUOTED":
        return t.text[1:-1].replace('""', '"')
    if t.kind == "WORD":
        return t.text.lower()
    return None


def _field(tokens: list[Token]) -> tuple[str, ...] | None:
    """Return the 1-3 identifier components; preserve schema when specified.

    Dropping the first component of ``schema.table.column`` would allow an
    unrelated schema to be silently treated as the configured TPC-H schema.
    """
    if not tokens or len(tokens) % 2 == 0:
        return None
    names: list[str] = []
    for i, token in enumerate(tokens):
        if i % 2:
            if token.text != ".":
                return None
        else:
            name = _name(token)
            if name is None:
                return None
            names.append(name)
    return tuple(names) if 1 <= len(names) <= 3 else None


def _literal(tokens: list[Token]) -> bool:
    # Only recognize constants, never arbitrary expressions or functions.
    if len(tokens) == 1:
        return tokens[0].kind in ("STRING", "NUMBER") or tokens[0].upper in ("TRUE", "FALSE")
    if len(tokens) == 2:
        return ((tokens[0].upper in ("DATE", "TIMESTAMP", "TIME") and tokens[1].kind == "STRING")
                or (tokens[0].text == "-" and tokens[1].kind == "NUMBER"))
    return False


def _trim_parens(tokens: list[Token]) -> list[Token]:
    while len(tokens) >= 2 and tokens[0].text == "(" and tokens[-1].text == ")":
        depth = 0
        wraps = True
        for i, t in enumerate(tokens):
            depth += (t.text == "(") - (t.text == ")")
            if depth == 0 and i != len(tokens) - 1:
                wraps = False
                break
        if not wraps:
            break
        tokens = tokens[1:-1]
    return tokens


def _conjuncts(tokens: list[Token]) -> list[list[Token]]:
    """Flatten *only* parenthesized AND groups, rejecting all OR expressions.

    Unlike a naive top-level split, this accepts ``(a AND b) AND (c AND d)``
    without ever treating an unsupported boolean expression as equivalent.
    """
    tokens = _trim_parens(tokens)
    if not tokens:
        raise ValueError("empty predicate / AND term")
    result: list[list[Token]] = []
    chunk: list[Token] = []
    depth = 0
    did_split = False
    for t in tokens:
        if t.kind == "WORD" and t.upper == "OR":
            raise ValueError("OR predicates are not supported (avoids unsafe index recommendations)")
        if t.text == "(":
            depth += 1
        elif t.text == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unmatched parentheses")
        if t.kind == "WORD" and t.upper == "AND" and depth == 0:
            if not chunk:
                raise ValueError("empty AND term")
            result.extend(_conjuncts(chunk))
            chunk = []
            did_split = True
        else:
            chunk.append(t)
    if depth:
        raise ValueError("unmatched parentheses")
    if not chunk:
        raise ValueError("empty AND term")
    if did_split:
        result.extend(_conjuncts(chunk))
        return result
    return [tokens]


def _tables(tokens: list[Token], schema: str) -> tuple[dict[str, tuple[str, str]], list[list[Token]]]:
    """Parse direct FROM + [INNER] JOIN ... ON chains; fail closed on bad JOINs.

    Mapping stores *one entry per FROM item*, not both alias and base name.
    This preserves SQL alias scoping and detects unqualified self-join ambiguity.
    """
    aliases: dict[str, tuple[str, str]] = {}
    joins: list[list[Token]] = []
    if not tokens:
        raise ValueError("missing FROM table")
    reserved = {"JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS", "OUTER",
                "NATURAL", "LATERAL", "ON", "USING", "WHERE", "AS"}

    def relation(at: int) -> int:
        if at >= len(tokens):
            raise ValueError("missing table name")
        name = _name(tokens[at])
        if name is None or tokens[at].upper in reserved:
            raise ValueError("only direct table names supported")
        at += 1
        table_schema = schema
        if at < len(tokens) and tokens[at].text == ".":
            if at + 1 >= len(tokens) or _name(tokens[at + 1]) is None:
                raise ValueError("invalid table name")
            table_schema, name = name, _name(tokens[at + 1])
            at += 2
        if table_schema != schema:
            raise ValueError(f"table schema {table_schema!r} is outside configured schema {schema!r}")
        alias = name
        if at < len(tokens) and tokens[at].upper == "AS":
            at += 1
            if at >= len(tokens) or _name(tokens[at]) is None or tokens[at].upper in reserved:
                raise ValueError("invalid table alias")
            alias = _name(tokens[at])
            at += 1
        elif (at < len(tokens) and tokens[at].kind in ("WORD", "QUOTED")
              and tokens[at].upper not in reserved):
            alias = _name(tokens[at])
            at += 1
        if alias in aliases:
            raise ValueError(f"duplicate table alias: {alias}")
        aliases[alias] = (table_schema, name)
        return at

    i = relation(0)
    while i < len(tokens):
        if tokens[i].upper == "INNER":
            i += 1
        if i >= len(tokens) or tokens[i].upper != "JOIN":
            raise ValueError("only INNER JOIN ... ON chains are supported")
        i = relation(i + 1)
        if i >= len(tokens) or tokens[i].upper != "ON":
            raise ValueError("INNER JOIN requires a nonempty ON clause")
        i += 1
        start = i
        depth = 0
        while i < len(tokens):
            t = tokens[i]
            if t.text == "(":
                depth += 1
            elif t.text == ")":
                depth -= 1
                if depth < 0:
                    raise ValueError("unmatched JOIN parentheses")
            if depth == 0 and (t.upper == "JOIN" or
                (t.upper == "INNER" and i + 1 < len(tokens) and tokens[i + 1].upper == "JOIN")):
                break
            i += 1
        if depth:
            raise ValueError("unmatched JOIN parentheses")
        if i == start:
            raise ValueError("INNER JOIN requires a nonempty ON clause")
        joins.append(tokens[start:i])
    return aliases, joins


def _resolve(tokens: list[Token], aliases: dict[str, tuple[str, str]],
             columns: Mapping[str, set[str]] | None) -> tuple[str, str, str] | None:
    parts = _field(tokens)
    if parts is None:
        return None
    col = parts[-1]
    if len(parts) == 1:
        # Do not deduplicate aliases by base table: self-joins still contain two
        # distinct relations, so unqualified columns in them are ambiguous.
        matching = [relation for relation in aliases.values()
                    if columns is None or col in columns.get(relation[1], set())]
        if len(matching) != 1:
            return None
        relation = matching[0]
    elif len(parts) == 2:
        relation = aliases.get(parts[0])
    else:
        # schema.table.column is allowed only when the reference is unaliased.
        relation = aliases.get(parts[1])
        if relation is None or relation != (parts[0], parts[1]):
            return None
    if relation is None or (columns is not None and col not in columns.get(relation[1], set())):
        return None
    return relation[0], relation[1], col


def _predicate(tokens: list[Token], aliases: dict[str, tuple[str, str]],
               columns: Mapping[str, set[str]] | None) -> list[Predicate]:
    found = [i for i, t in enumerate(tokens) if t.text in OPERATORS]
    if len(found) != 1:
        raise ValueError("unsupported predicate expression")
    pos = found[0]
    op = tokens[pos].text
    left, right = tokens[:pos], tokens[pos + 1:]
    lcol, rcol = _resolve(left, aliases, columns), _resolve(right, aliases, columns)
    if lcol and rcol and op == "=":
        # Join equality can support an indexed nested-loop or merge plan.
        return [Predicate(*lcol, "join", op), Predicate(*rcol, "join", op)]
    if lcol and _literal(right):
        return [Predicate(*lcol, "equality" if op == "=" else "range", op)]
    if rcol and _literal(left):
        # Predicates identify the column, so normalize literal OP column into
        # column REVERSED_OP literal (e.g. 10 <= price means price >= 10).
        reversed_op = {"=": "=", "<": ">", "<=": ">=", ">": "<", ">=": "<="}[op]
        return [Predicate(*rcol, "equality" if op == "=" else "range", reversed_op)]
    raise ValueError("predicate is not a supported column-to-literal comparison or equijoin")


def parse_workload(source: str, schema: str = "tpch", *,
                   columns: Mapping[str, set[str]] | None = None,
                   weights: Mapping[int, float] | None = None) -> ParseResult:
    """Parse simple SELECT queries. Unsupported statements/terms are warned/skipped.

    weights use 1-based statement numbers. A query with a non-positive weight is invalid.
    Column maps should come from PostgreSQL or the known benchmark schema; without
    them, ambiguous unqualified columns in joins cannot be resolved safely.
    """
    queries: list[WorkloadQuery] = []
    warnings: list[str] = []
    for n, statement in enumerate(split_statements(source), 1):
        try:
            if not statement or statement[0].upper != "SELECT":
                raise ValueError("only SELECT statements supported")
            if any(t.upper in ("SELECT", "WITH", "UNION", "INTERSECT", "EXCEPT") for t in statement[1:]):
                raise ValueError("subqueries, CTEs and set operations not supported")
            weight = float((weights or {}).get(n, 1.0))
            if not 0 < weight < float("inf"):
                raise ValueError("query weight must be positive and finite")
            if any(t.kind == "OTHER" for t in statement):
                raise ValueError("unrecognized SQL token")
            depth = 0
            positions: dict[str, int] = {}
            for i, t in enumerate(statement):
                if depth == 0 and t.kind == "WORD" and t.upper in ("FROM", "WHERE"):
                    if t.upper in positions:
                        raise ValueError(f"duplicate {t.upper} clause")
                    positions[t.upper] = i
                depth += (t.text == "(") - (t.text == ")")
                if depth < 0:
                    raise ValueError("unmatched parentheses")
            if depth:
                raise ValueError("unmatched parentheses")
            if "FROM" not in positions:
                raise ValueError("missing FROM clause")
            from_pos = positions["FROM"]
            if from_pos < 2:
                raise ValueError("SELECT requires an expression before FROM")
            where_pos = positions.get("WHERE", len(statement))
            if where_pos < from_pos:
                raise ValueError("WHERE before FROM")
            end = next((i for i in range(from_pos + 1, len(statement)) if statement[i].upper in STOP), len(statement))
            aliases, joins = _tables(statement[from_pos + 1:end], schema)
            conditions: list[list[Token]] = []
            if "WHERE" in positions:
                start = where_pos + 1
                stop = next((i for i in range(start, len(statement)) if statement[i].upper in STOP - {"WHERE"}), len(statement))
                conditions = _conjuncts(statement[start:stop])
            for j in joins:
                conditions += _conjuncts(j)
            predicates: list[Predicate] = []
            for cond in conditions:
                predicates.extend(_predicate(cond, aliases, columns))
            if not predicates:
                raise ValueError("no supported predicates")
            queries.append(WorkloadQuery(n, " ".join(t.text for t in statement), weight, tuple(dict.fromkeys(predicates))))
        except (ValueError, OverflowError) as exc:
            warnings.append(f"Query {n} skipped: {exc}")
    return ParseResult(tuple(queries), tuple(warnings))


def load_workload(path: Path, **kwargs) -> ParseResult:
    return parse_workload(path.read_text(encoding="utf-8-sig"), **kwargs)
