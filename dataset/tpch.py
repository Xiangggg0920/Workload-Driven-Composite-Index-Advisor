"""Generate TPC-H CSV files and load the PostgreSQL benchmark tables."""

import argparse
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent
TABLES = ("orders", "lineitem")


def scale_factor(value):
    try:
        scale = Decimal(value)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("scale must be a number") from None
    if not scale.is_finite() or not Decimal("0.01") <= scale <= 100:
        raise argparse.ArgumentTypeError("scale must be between 0.01 and 100")
    return scale


def generate(scale, output):
    import duckdb

    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"Choose a new output directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent, prefix=".tpch-") as temp:
        temp = Path(temp)
        files = temp / "csv"
        files.mkdir()
        config = {"extension_directory": str(output.parent / ".duckdb-extensions")}
        with duckdb.connect(str(temp / "tpch.duckdb"), config=config) as db:
            db.execute("INSTALL tpch")
            db.execute("LOAD tpch")
            print(f"Generating TPC-H SF{scale}...", flush=True)
            db.execute(f"CALL dbgen(sf = {scale:f})")
            for table in TABLES:
                print(f"Exporting {table}...", flush=True)
                destination = (files / f"{table}.csv").as_posix().replace("'", "''")
                db.execute(f"COPY {table} TO '{destination}' (FORMAT CSV, HEADER FALSE)")
        files.rename(output)
    print(f"TPC-H SF{scale} CSV files: {output}")


def load(source, dsn):
    import psycopg

    for table in TABLES:
        path = source / f"{table}.csv"
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Missing or empty CSV: {path}")

    counts = {}
    with psycopg.connect(dsn) as db, db.cursor() as cursor:
        cursor.execute((HERE / "schema.sql").read_text(encoding="utf-8"))
        for table in TABLES:
            print(f"Loading {table}...", flush=True)
            with (source / f"{table}.csv").open("rb") as stream:
                with cursor.copy(f"COPY tpch.{table} FROM STDIN (FORMAT CSV)") as copy:
                    while block := stream.read(1024 * 1024):
                        copy.write(block)
            counts[table] = cursor.rowcount
            cursor.execute(f"ANALYZE tpch.{table}")

    for table, count in counts.items():
        print(f"tpch.{table}: {count:,} rows")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate_parser = commands.add_parser("generate", help="generate two CSV files")
    generate_parser.add_argument("--scale", required=True, type=scale_factor)
    generate_parser.add_argument("--output", required=True, type=Path)
    load_parser = commands.add_parser("load", help="load CSV files into PostgreSQL")
    load_parser.add_argument("--source", required=True, type=Path)
    load_parser.add_argument(
        "--dsn", default="", help="PostgreSQL connection string (defaults to libpq environment)"
    )
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.scale, args.output)
    else:
        load(args.source, args.dsn)


if __name__ == "__main__":
    main()
