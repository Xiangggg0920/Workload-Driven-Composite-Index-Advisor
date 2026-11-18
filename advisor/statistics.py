"""Read PostgreSQL planner statistics; never change database contents."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ColumnStats:
    n_distinct: float
    null_frac: float
    avg_width: int


@dataclass(frozen=True)
class TableStats:
    schema: str
    table: str
    rows: float
    heap_bytes: int
    columns: Mapping[str, ColumnStats]

    @property
    def heap_pages(self) -> float:
        return max(1.0, self.heap_bytes / 8192.0)


def read_statistics(connection, schema: str = "tpch") -> dict[str, TableStats]:
    """Read pg_class + pg_stats for all ordinary tables in the requested schema."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.relname, c.reltuples::float8, pg_relation_size(c.oid)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relkind IN ('r', 'p')
            ORDER BY c.relname
        """, (schema,))
        rows = cursor.fetchall()
        if not rows:
            raise RuntimeError(f"No tables found in schema {schema!r}; check .env and dataset import")
        tables = {}
        for name, reltuples, size in rows:
            cursor.execute("""
                SELECT attname, n_distinct, null_frac, avg_width
                FROM pg_stats WHERE schemaname = %s AND tablename = %s
            """, (schema, name))
            cols = {col: ColumnStats(float(distinct or 0), float(null or 0), int(width or 8))
                    for col, distinct, null, width in cursor.fetchall()}
            if not cols or float(reltuples) <= 0:
                raise RuntimeError(f"Statistics for {schema}.{name} are unavailable. Run ANALYZE on this table.")
            tables[name] = TableStats(schema, name, float(reltuples), int(size), cols)
        return tables
