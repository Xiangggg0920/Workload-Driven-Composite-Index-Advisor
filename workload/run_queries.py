"""Run read-only SQL queries using the project's connection settings."""

import argparse
import csv
from pathlib import Path
import sys

import psycopg
from dotenv import load_dotenv


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sql_file", nargs="?", type=Path, default=directory / "smoke.sql",
        help="SQL file to run (default: workload/smoke.sql)",
    )
    args = parser.parse_args()
    sql = args.sql_file.read_text(encoding="utf-8-sig")
    load_dotenv(directory.parent / ".env")

    output = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    with psycopg.connect() as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute(sql)
            while True:
                if cursor.description is not None:
                    output.writerow(column.name for column in cursor.description)
                    output.writerows(cursor)
                else:
                    print(cursor.statusmessage)
                if not cursor.nextset():
                    break


if __name__ == "__main__":
    main()
