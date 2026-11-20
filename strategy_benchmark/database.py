"""PostgreSQL boundary: dry-run connections cannot reach any index mutation."""
from __future__ import annotations

from contextlib import contextmanager
import shutil

import psycopg
from psycopg.pq import TransactionStatus

from dataset.prepare_sf1 import ROOT, TARGET
from .plan import digest, quote, create_ddl, drop_ddl


class SafetyError(RuntimeError):
    pass


class OverBudget(RuntimeError):
    def __init__(self, records, budget):
        super().__init__("Measured index bytes exceed budget; entire configuration rolled back")
        self.records, self.budget = records, budget


def owned(index, entry, tag, role):
    spec = entry["spec"]
    return (index["schema"] == spec["schema"] and index["name"] == spec["name"]
        and index["table_schema"] == "tpch" and index["table"] == spec["table"]
        and index["columns"] == spec["columns"] and index["method"] == "btree"
        and index["nkeys"] == index["natts"] == len(spec["columns"])
        and not index["unique"] and not index["primary"] and not index["constraint"]
        and index["valid"] and index["ready"] and index["predicate"] is None
        and index["expressions"] is None and index["comment"] == tag and index["owner"] == role
        and (entry.get("oid") is None or index["oid"] == entry["oid"])
        and (entry.get("definition") is None or index["definition"] == entry["definition"])
        and (entry.get("table_oid") is None or index["table_oid"] == entry["table_oid"]))


class Database:
    def __init__(self, *, allow_write=False):
        self.allow_write = allow_write
        self.conn = psycopg.connect(dbname=TARGET, autocommit=True, connect_timeout=5,
                                    prepare_threshold=None, application_name="group9_strategy_benchmark")
        self.conn.read_only = not allow_write
        self.identity = self.get_identity()
        if self.identity["database"] != TARGET:
            self.close()
            raise SafetyError("Only advisor_benchmark is allowed")

    def close(self):
        self.conn.close()

    def rows(self, query, params=None):
        if not query.lstrip().upper().startswith(("SELECT", "SHOW")):
            raise SafetyError("Read API accepts only fixed SELECT/SHOW statements")
        if self.conn.info.transaction_status == TransactionStatus.IDLE:
            with self.conn.transaction(force_rollback=True):
                self.conn.execute("SET TRANSACTION READ ONLY")
                self.conn.execute("SET LOCAL statement_timeout = 300000")
                return self.rows(query, params)
        with self.conn.cursor() as cursor:
            cursor.execute(query, params, binary=True, prepare=False)
            return cursor.fetchall()

    def write(self, command):
        if not self.allow_write:
            raise SafetyError("DDL/locks disabled: this is a read-only dry-run connection")
        self.conn.execute(command, prepare=False)

    def get_identity(self):
        row = self.rows("SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),"
                        "(SELECT system_identifier::text FROM pg_control_system()),current_setting('server_version'),"
                        "inet_server_addr()::text,inet_server_port(),current_user")[0]
        return dict(zip(("database", "database_oid", "system_identifier", "server_version", "address", "port", "role"), row))

    def indexes(self):
        data = self.rows("""SELECT ic.oid,ins.nspname,ic.relname,tns.nspname,tc.relname,tc.oid,am.amname,
            ARRAY(SELECT a.attname FROM unnest(ix.indkey) WITH ORDINALITY k(attnum,position)
                  JOIN pg_attribute a ON a.attrelid=tc.oid AND a.attnum=k.attnum ORDER BY k.position),
            ix.indnkeyatts,ix.indnatts,ix.indisunique,ix.indisprimary,ix.indisvalid,ix.indisready,
            pg_get_expr(ix.indpred,ix.indrelid),pg_get_expr(ix.indexprs,ix.indrelid),
            obj_description(ic.oid,'pg_class'),pg_get_indexdef(ic.oid),pg_relation_size(ic.oid),
            pg_total_relation_size(ic.oid),pg_get_userbyid(ic.relowner),
            EXISTS(SELECT 1 FROM pg_constraint co WHERE co.conindid=ic.oid)
            FROM pg_index ix JOIN pg_class ic ON ic.oid=ix.indexrelid
            JOIN pg_namespace ins ON ins.oid=ic.relnamespace JOIN pg_class tc ON tc.oid=ix.indrelid
            JOIN pg_namespace tns ON tns.oid=tc.relnamespace JOIN pg_am am ON am.oid=ic.relam
            WHERE tns.nspname='tpch' ORDER BY ins.nspname,ic.relname""")
        keys = ("oid", "schema", "name", "table_schema", "table", "table_oid", "method", "columns",
                "nkeys", "natts", "unique", "primary", "valid", "ready", "predicate", "expressions",
                "comment", "definition", "main_bytes", "total_bytes", "owner", "constraint")
        return [dict(zip(keys, row)) for row in data]

    def statistics_signature(self):
        return digest([r[0] for r in self.rows("SELECT row_to_json(s)::text FROM pg_stats s "
                     "WHERE schemaname='tpch' ORDER BY tablename,attname,inherited")])

    def settings(self):
        return dict(self.rows("SELECT name,setting FROM pg_settings WHERE name LIKE 'enable_%' OR name IN "
            "('work_mem','jit','max_parallel_workers_per_gather','random_page_cost','seq_page_cost',"
            "'effective_cache_size','effective_io_concurrency','cpu_tuple_cost','cpu_index_tuple_cost',"
            "'cpu_operator_cost','default_statistics_target','track_io_timing','plan_cache_mode',"
            "'shared_buffers','search_path','server_encoding','lc_collate','lc_ctype') ORDER BY name"))

    def capture(self):
        tables = self.rows("SELECT c.oid,c.relname,ARRAY(SELECT a.attname FROM pg_attribute a WHERE "
            "a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum), "
            "ARRAY(SELECT a.attname||':'||format_type(a.atttypid,a.atttypmod)||':'||a.attnotnull::text||':'||a.attcollation::text "
            "FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum), "
            "c.relpages,c.relallvisible "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='tpch' AND c.relkind='r' ORDER BY c.relname")
        active = self.rows("SELECT backend_type,state,count(*) FROM pg_stat_activity WHERE datname=current_database() "
            "AND pid<>pg_backend_pid() AND (backend_type='autovacuum worker' OR "
            "(backend_type='client backend' AND state<>'idle')) GROUP BY backend_type,state")
        return {"identity": self.identity, "indexes": self.indexes(),
            "tables": [{"oid": oid, "name": name, "columns": cols, "column_types": types}
                       for oid, name, cols, types, pages, visible in tables],
            "table_visibility": [[name, pages, visible] for oid, name, cols, types, pages, visible in tables],
            "settings": self.settings(), "column_statistics_sha256": self.statistics_signature(),
            "active_other_backends": active, "disk_free_bytes": shutil.disk_usage(ROOT).free}

    def maintenance(self):
        return [[str(v) for v in row] for row in self.rows("SELECT relname,last_analyze,last_autoanalyze,"
            "last_autovacuum,n_tup_ins,n_tup_upd,n_tup_del FROM pg_stat_all_tables "
            "WHERE schemaname='tpch' ORDER BY relname")]

    def acquire(self):
        if not self.allow_write:
            raise SafetyError("Execution lock is not acquired during dry-run")
        if not self.rows("SELECT pg_try_advisory_lock(917309,3003)")[0][0]:
            raise SafetyError("Another strategy experiment is running")

    def release(self):
        if self.allow_write:
            self.rows("SELECT pg_advisory_unlock(917309,3003)")

    @contextmanager
    def guard_data(self):
        with self.conn.transaction(force_rollback=True):
            self.write("SET LOCAL lock_timeout = '5s'")
            self.write('LOCK TABLE "tpch"."lineitem", "tpch"."orders" IN SHARE MODE')
            yield

    def data_signature(self):
        result = {}
        for table in ("orders", "lineitem"):
            row = self.rows(f"SELECT count(*),sum(hashtextextended(row_to_json(t)::text,0)::numeric),"
                            f"sum(hashtextextended(row_to_json(t)::text,917309)::numeric) FROM tpch.{quote(table)} t")[0]
            result[table] = [str(value) for value in row]
        return result

    def build(self, specs, budget, tag):
        records = []
        with self.conn.transaction():
            self.write("SET LOCAL lock_timeout = '5s'")
            self.write("SET LOCAL statement_timeout = '15min'")
            self.write('LOCK TABLE "tpch"."lineitem", "tpch"."orders" IN SHARE MODE')
            occupied = {i["name"] for i in self.indexes()}
            if occupied.intersection(s["name"] for s in specs):
                raise SafetyError("Index name already exists; never adopt or overwrite it")
            for spec in specs:
                self.write(create_ddl(spec))
                literal = "'" + tag.replace("'", "''") + "'"
                self.write(f"COMMENT ON INDEX {quote(spec['schema'])}.{quote(spec['name'])} IS {literal}")
                index = next(i for i in self.indexes() if i["name"] == spec["name"])
                if not owned(index, {"spec": spec}, tag, self.identity["role"]):
                    raise SafetyError("New index definition/ownership verification failed")
                records.append(index)
                if sum(i["main_bytes"] for i in records) > budget:
                    raise OverBudget(records, budget)
        return records

    def cleanup(self, entries, tag):
        """Validate ALL ownership before ANY DROP, with table locks closing races."""
        active = [e for e in entries if e["state"] in ("pending", "committed", "cleanup_failed")]
        if not active:
            return []
        dropped = []
        with self.conn.transaction():
            self.write("SET LOCAL lock_timeout = '5s'")
            self.write("SET LOCAL statement_timeout = '1min'")
            self.write('LOCK TABLE "tpch"."lineitem", "tpch"."orders" IN ACCESS EXCLUSIVE MODE')
            actual = self.indexes()
            by_name = {i["name"]: i for i in actual}
            to_drop = []
            for entry in active:
                index = by_name.get(entry["spec"]["name"])
                if index is None:
                    if any(i["oid"] == entry.get("oid") for i in actual):
                        raise SafetyError("Owned index was renamed; manual review required")
                    continue
                if not owned(index, entry, tag, self.identity["role"]):
                    raise SafetyError("Cleanup refused: OID/tag/definition/owner mismatch")
                to_drop.append(entry["spec"])
            for spec in to_drop:
                self.write(drop_ddl(spec))
                dropped.append(spec["name"])
        return dropped


def verify_environment(plan, environment):
    if environment["identity"] != plan["database"]:
        raise SafetyError("Database/cluster/role identity changed")
    if environment["tables"] != plan["environment"]["tables"]:
        raise SafetyError("Table identities/schema changed")
    if environment.get("table_visibility") != plan["environment"].get("table_visibility"):
        raise SafetyError("Heap page/visibility statistics changed; review a new plan")
    if environment["settings"] != plan["environment"]["settings"]:
        raise SafetyError("Planner/session settings changed")
    if environment["column_statistics_sha256"] != plan["environment"]["column_statistics_sha256"]:
        raise SafetyError("Column statistics changed; regenerate and review the plan")
    if environment["indexes"] != plan["environment"]["indexes"]:
        raise SafetyError("Unexpected indexes; do not remove them")
    if environment["active_other_backends"]:
        raise SafetyError("Other active clients/maintenance detected; use an exclusive experiment window")
    if environment["disk_free_bytes"] < 10 * 1024**3:
        raise SafetyError("Less than 10 GiB free")
