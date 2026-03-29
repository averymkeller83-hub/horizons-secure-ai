#!/usr/bin/env python3
"""Database migration script — applies schema.sql to PostgreSQL.

Usage:
    python scripts/migrate.py
    python scripts/migrate.py --db-url postgresql://user:pass@host:5432/dbname
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Apply database schema")
    parser.add_argument(
        "--db-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://horizons:horizons_dev_password@localhost:5432/horizons",
        ),
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--schema",
        default=str(Path(__file__).resolve().parent.parent / "db" / "schema.sql"),
        help="Path to schema SQL file",
    )
    args = parser.parse_args()

    # Strip async driver prefix if present
    db_url = args.db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        import psycopg2
    except ImportError:
        print("Installing psycopg2-binary...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
        import psycopg2

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        sys.exit(1)

    schema_sql = schema_path.read_text()

    print(f"Connecting to database...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    print(f"Applying schema from {schema_path}...")
    cur.execute(schema_sql)

    print("Schema applied successfully.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
