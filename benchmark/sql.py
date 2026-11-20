"""Split PostgreSQL SQL without changing literals, comments or quoted names.

This is a lexical splitter, not a SQL grammar or a security sandbox. PostgreSQL
validates query syntax and enforces READ ONLY independently of this module.
Ordinary strings use standard_conforming_strings=on, also enforced by the runner.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Statement:
    sql: str
    words: tuple[str, ...]


class WorkloadError(ValueError):
    pass


_DOLLAR = re.compile(r"\$(?:[^\W\d][\w]*)?\$", re.UNICODE)
# Reject these anywhere outside quoted text, including inside WITH clauses.
# The server-side read-only transaction is still mandatory: a SELECT can invoke
# a function which attempts to write, without containing any of these keywords.
_DISALLOWED = frozenset("""
    INSERT UPDATE DELETE MERGE INTO CREATE ALTER DROP TRUNCATE COPY CALL DO
    EXECUTE PREPARE DEALLOCATE GRANT REVOKE VACUUM ANALYZE EXPLAIN REFRESH
    REINDEX CLUSTER LOCK SET RESET BEGIN START COMMIT ROLLBACK SAVEPOINT
    RELEASE DISCARD CHECKPOINT LISTEN UNLISTEN NOTIFY LOAD IMPORT
""".split())


def split_workload(source: str) -> list[Statement]:
    """Ignore empty/comment-only statements; accept a final missing semicolon.

    Handle doubled quotes, E-string escapes, dollar quotes and nested block
    comments. An unterminated construct rejects the whole file before execution.
    """
    source = source.removeprefix("\ufeff")
    statements = []
    start = i = 0
    words: list[str] = []
    has_code = False
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
            continue
        if source.startswith("--", i):
            end = re.search(r"[\r\n]", source[i + 2:])
            i = len(source) if end is None else i + 2 + end.end()
            continue
        if source.startswith("/*", i):
            depth = 1
            i += 2
            while i < len(source) and depth:
                if source.startswith("/*", i):
                    depth += 1
                    i += 2
                elif source.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise WorkloadError("Unterminated block comment")
            continue
        if char == ";":
            if has_code:
                statements.append(Statement(source[start:i].strip(), tuple(words)))
            start = i = i + 1
            words = []
            has_code = False
            continue
        has_code = True
        if char in "'\"":
            escaped = (char == "'" and i > 0 and source[i - 1] in "eE"
                       and (i < 2 or not (source[i - 2].isalnum() or source[i - 2] in "_$")))
            i += 1
            while i < len(source):
                if escaped and source[i] == "\\":
                    i += 2
                elif source[i] == char:
                    if i + 1 < len(source) and source[i + 1] == char:
                        i += 2
                    else:
                        i += 1
                        break
                else:
                    i += 1
            else:
                raise WorkloadError("Unterminated quoted string or identifier")
            continue
        if char == "$" and (match := _DOLLAR.match(source, i)):
            end = source.find(match.group(), match.end())
            if end < 0:
                raise WorkloadError("Unterminated dollar-quoted string")
            i = end + len(match.group())
            continue
        if char.isalpha() or char == "_":
            end = i + 1
            while end < len(source) and (source[end].isalnum() or source[end] in "_$"):
                end += 1
            words.append(source[i:end].upper())
            i = end
            continue
        i += 1
    if has_code:
        statements.append(Statement(source[start:].strip(), tuple(words)))
    return statements


def validate_query(statement: Statement) -> None:
    """Conservative lexical preflight; READ ONLY is the execution safeguard."""
    if not statement.words or statement.words[0] not in {"SELECT", "WITH", "VALUES", "TABLE"}:
        raise WorkloadError("Only SELECT, read-only WITH, VALUES and TABLE queries are accepted")
    forbidden = _DISALLOWED.intersection(statement.words)
    if forbidden:
        raise WorkloadError("Non-read-only/unsupported SQL keyword: " + ", ".join(sorted(forbidden)))
