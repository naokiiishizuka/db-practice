#!/usr/bin/env python3
import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from dotenv import load_dotenv
import psycopg

BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BASE_DIR / "migrations"
SEEDS_DIR = BASE_DIR / "seeds"
SQL_DIR = BASE_DIR / "sql"
MIGRATION_PATTERN = re.compile(
    r"^(?P<version>\d{4,})_(?P<name>[a-zA-Z0-9_]+)\.(?P<direction>up|down)\.sql$"
)
SEED_PATTERN = re.compile(r"^(?P<version>\d{3,})_(?P<name>[a-zA-Z0-9_]+)\.sql$")


@dataclass
class Migration:
    version: int
    name: str
    up_path: Path
    down_path: Path


@dataclass
class SeedFile:
    version: int
    name: str
    path: Path


def load_environment() -> None:
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()


def require_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set. Update .env first.")
    return url


def ensure_migrations_dir() -> None:
    if not MIGRATIONS_DIR.exists():
        MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_seeds_dir() -> None:
    if not SEEDS_DIR.exists():
        SEEDS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_sql_dir() -> None:
    if not SQL_DIR.exists():
        SQL_DIR.mkdir(parents=True, exist_ok=True)


def discover_migrations() -> List[Migration]:
    ensure_migrations_dir()
    buckets: dict[int, dict[str, Path]] = {}
    for path in MIGRATIONS_DIR.glob("*.sql"):
        match = MIGRATION_PATTERN.match(path.name)
        if not match:
            raise SystemExit(f"Invalid migration filename: {path.name}")
        version = int(match["version"])
        buckets.setdefault(version, {"name": match["name"]})
        if buckets[version].get("name") != match["name"]:
            raise SystemExit(f"Conflicting names for version {version}")
        buckets[version][match["direction"]] = path

    migrations: List[Migration] = []
    for version in sorted(buckets):
        entry = buckets[version]
        up_path = entry.get("up")
        down_path = entry.get("down")
        if not up_path or not down_path:
            raise SystemExit(f"Missing up/down file for version {version}")
        migrations.append(
            Migration(
                version=version,
                name=entry["name"],
                up_path=up_path,
                down_path=down_path,
            )
        )
    return migrations


def discover_seeds() -> List[SeedFile]:
    ensure_seeds_dir()
    seeds: List[SeedFile] = []
    for path in sorted(SEEDS_DIR.glob("*.sql")):
        match = SEED_PATTERN.match(path.name)
        if not match:
            raise SystemExit(f"Invalid seed filename: {path.name}")
        version = int(match["version"])
        seeds.append(SeedFile(version=version, name=match["name"], path=path))
    return sorted(seeds, key=lambda s: s.version)


def ensure_schema_table(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    conn.commit()


def read_sql_file(path: Path) -> str:
    sql = path.read_text(encoding="utf-8").strip()
    if not sql:
        raise SystemExit(f"Migration file is empty: {path}")
    return sql


def read_raw_sql(
    input_path: Optional[str] = None,
    inline_query: Optional[str] = None,
    named_query: Optional[str] = None,
) -> str:
    if input_path:
        path = Path(input_path)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        if not path.exists():
            raise SystemExit(f"SQL file not found: {path}")
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise SystemExit(f"SQL file is empty: {path}")
        return content
    if named_query:
        ensure_sql_dir()
        filename = named_query if named_query.endswith(".sql") else f"{named_query}.sql"
        path = SQL_DIR / filename
        if not path.exists():
            raise SystemExit(f"SQL preset not found: {path}")
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise SystemExit(f"SQL file is empty: {path}")
        return content
    if inline_query:
        return inline_query.strip()
    raise SystemExit("Either --file, --query, or --name must be provided.")


def format_value(value: object) -> str:
    if value is None:
        return "NULL"
    return str(value)


def print_result_table(columns: List[str], rows: List[List[object]]) -> None:
    if not columns:
        print("(no columns)")
        return
    str_rows = [[format_value(value) for value in row] for row in rows]
    widths = [len(col) for col in columns]
    for row in str_rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))
    header = " | ".join(col.ljust(widths[idx]) for idx, col in enumerate(columns))
    print(header)
    print("-+-".join("-" * width for width in widths))
    for row in str_rows:
        print(" | ".join(value.ljust(widths[idx]) for idx, value in enumerate(row)))
    if not rows:
        print("(0 rows)")


def run_sql(conn: psycopg.Connection, sql: str) -> None:
    with conn.transaction():
        cur = conn.execute(sql, prepare=False)
        if cur.description:
            columns = [desc.name or f"column_{idx}" for idx, desc in enumerate(cur.description)]
            rows = cur.fetchall()
            print_result_table(columns, rows)
            print(f"\n{len(rows)} row(s).")
        else:
            affected = cur.rowcount if cur.rowcount != -1 else 0
            print(f"Command completed. {affected} row(s) affected.")


def apply_up(conn: psycopg.Connection, target: Optional[int]) -> None:
    migrations = discover_migrations()
    ensure_schema_table(conn)
    applied_versions = {
        row[0] for row in conn.execute("SELECT version FROM schema_migrations")
    }

    for migration in migrations:
        if target is not None and migration.version > target:
            break
        if migration.version in applied_versions:
            continue
        sql = read_sql_file(migration.up_path)
        with conn.transaction():
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (%s, %s)",
                (migration.version, migration.name),
            )
        print(f"Applied {migration.version:04d}_{migration.name}")


def apply_down(conn: psycopg.Connection, steps: int) -> None:
    if steps <= 0:
        print("Nothing to roll back.")
        return
    ensure_schema_table(conn)
    cur = conn.execute(
        "SELECT version, name FROM schema_migrations ORDER BY version DESC"
    )
    applied = cur.fetchall()
    if not applied:
        print("No migrations have been applied.")
        return

    count = 0
    migrations = {m.version: m for m in discover_migrations()}
    for version, name in applied:
        if count >= steps:
            break
        migration = migrations.get(version)
        if not migration:
            raise SystemExit(f"Missing migration files for version {version}")
        sql = read_sql_file(migration.down_path)
        with conn.transaction():
            conn.execute(sql)
            conn.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
        print(f"Reverted {version:04d}_{name}")
        count += 1


def show_version(conn: psycopg.Connection) -> None:
    ensure_schema_table(conn)
    cur = conn.execute(
        "SELECT version, name FROM schema_migrations ORDER BY version DESC LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        print("No migrations applied.")
    else:
        print(f"{int(row[0]):04d}_{row[1]}")


def show_status(conn: psycopg.Connection) -> None:
    migrations = discover_migrations()
    ensure_schema_table(conn)
    applied = {
        row[0]: row[2]
        for row in conn.execute(
            "SELECT version, name, applied_at FROM schema_migrations ORDER BY version"
        )
    }

    for migration in migrations:
        if migration.version in applied:
            applied_at = applied[migration.version]
            print(f"[X] {migration.version:04d}_{migration.name} ({applied_at})")
        else:
            print(f"[ ] {migration.version:04d}_{migration.name}")


def create_migration(name: str) -> None:
    ensure_migrations_dir()
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip()).strip("_").lower()
    if not normalized:
        raise SystemExit("Migration name must contain alphanumeric characters.")
    migrations = discover_migrations()
    next_version = (migrations[-1].version + 1) if migrations else 1
    version_str = f"{next_version:04d}"
    base_filename = f"{version_str}_{normalized}"
    up_path = MIGRATIONS_DIR / f"{base_filename}.up.sql"
    down_path = MIGRATIONS_DIR / f"{base_filename}.down.sql"
    template = "-- Write your SQL here\n"
    up_path.write_text(template, encoding="utf-8")
    down_path.write_text(template, encoding="utf-8")
    print(f"Created {up_path.name} and {down_path.name}")


def create_seed(name: str) -> None:
    ensure_seeds_dir()
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip()).strip("_").lower()
    if not normalized:
        raise SystemExit("Seed name must contain alphanumeric characters.")
    seeds = discover_seeds()
    next_version = (seeds[-1].version + 1) if seeds else 1
    version_str = f"{next_version:03d}"
    filename = f"{version_str}_{normalized}.sql"
    path = SEEDS_DIR / filename
    template = "-- Insert seed data here\n"
    path.write_text(template, encoding="utf-8")
    print(f"Created seed file {filename}")


def run_seeds(conn: psycopg.Connection, name: Optional[str]) -> None:
    seeds = discover_seeds()
    if not seeds:
        print("No seed files found in ./seeds")
        return
    for seed in seeds:
        identifier = f"{seed.version:03d}_{seed.name}"
        if name and identifier != name:
            continue
        sql = read_sql_file(seed.path)
        with conn.transaction():
            conn.execute(sql)
        print(f"Ran seed {identifier}")
    if name:
        matching = any(f"{seed.version:03d}_{seed.name}" == name for seed in seeds)
        if not matching:
            raise SystemExit(f"Seed file matching '{name}' not found.")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple PostgreSQL migration runner.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    up_parser = subparsers.add_parser("up", help="Apply pending migrations")
    up_parser.add_argument(
        "--target",
        type=int,
        default=None,
        help="Apply up to and including the specified version number",
    )

    down_parser = subparsers.add_parser("down", help="Rollback migrations")
    down_parser.add_argument(
        "steps", type=int, nargs="?", default=1, help="Number of steps to rollback"
    )

    subparsers.add_parser("version", help="Show current migration version")
    subparsers.add_parser("status", help="List applied and pending migrations")

    create_parser = subparsers.add_parser("create", help="Generate new migration files")
    create_parser.add_argument("name", help="Name for the migration (snake_case)")

    seed_parser = subparsers.add_parser("seed", help="Manage seed SQL files")
    seed_sub = seed_parser.add_subparsers(dest="seed_command", required=True)

    seed_run = seed_sub.add_parser("run", help="Execute seed SQL files")
    seed_run.add_argument(
        "--name",
        help="Specific seed identifier to run (e.g. 001_initial_data). Runs all if omitted.",
    )

    seed_create = seed_sub.add_parser("create", help="Generate a new seed SQL file")
    seed_create.add_argument("name", help="Name for the seed file")

    sql_parser = subparsers.add_parser(
        "sql", help="Run arbitrary SQL and print the results to the terminal"
    )
    sql_source = sql_parser.add_mutually_exclusive_group(required=True)
    sql_source.add_argument(
        "-q",
        "--query",
        help="Inline SQL to execute (wrap in quotes). Example: --query \"SELECT * FROM users\"",
    )
    sql_source.add_argument(
        "-f",
        "--file",
        help="Path to a .sql file containing statements to execute",
    )
    sql_source.add_argument(
        "-n",
        "--name",
        help="Name of a SQL file under ./sql (extension optional)",
    )

    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    load_environment()

    if args.command == "create":
        create_migration(args.name)
        return
    if args.command == "seed" and args.seed_command == "create":
        create_seed(args.name)
        return
    if args.command == "sql":
        sql_text = read_raw_sql(
            input_path=args.file,
            inline_query=args.query,
            named_query=args.name,
        )
    else:
        sql_text = None

    database_url = require_database_url()
    with psycopg.connect(database_url) as conn:
        if args.command == "up":
            apply_up(conn, args.target)
        elif args.command == "down":
            apply_down(conn, args.steps)
        elif args.command == "version":
            show_version(conn)
        elif args.command == "status":
            show_status(conn)
        elif args.command == "seed" and args.seed_command == "run":
            run_seeds(conn, args.name)
        elif args.command == "sql":
            run_sql(conn, sql_text)
        else:
            raise SystemExit(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
