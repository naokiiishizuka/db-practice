## DB Practice Environment

This repository contains a minimal Docker-based setup for experimenting with relational databases and schema migrations. It uses PostgreSQL as the primary database and a lightweight Python runner (`scripts/migrate.py`) to apply SQL files in order.

### Prerequisites

- Docker and Docker Compose

### Getting Started

1. Copy `.env.example` to `.env` and adjust credentials if needed.
2. Start the PostgreSQL container:
   ```bash
   docker compose up -d db
   ```
3. Apply migrations with the Python runner (it runs inside a Docker container so you do not need Python locally):
   ```bash
   ./scripts/migrate.sh up
   ```
4. To roll back the latest migration:
   ```bash
   ./scripts/migrate.sh down 1
   ```
5. View database logs if needed:
   ```bash
   docker compose logs -f db
   ```

### Working With Migrations

- Create new migration files with:
  ```bash
  ./scripts/migrate.sh create add_new_table
  ```
  This generates the matching `*.up.sql` and `*.down.sql` files under `./migrations`, so you do not have to create them manually.
- Edit those files to describe the schema changes. The runner applies every `*.up.sql` file in numerical order and records its progress in the `schema_migrations` table.

### Seeding Data

- Seed files live under `./seeds` and follow the naming pattern `NNN_name.sql`.
- Run all seeds (after applying migrations) with:
  ```bash
  ./scripts/migrate.sh seed run
  ```
- Run a specific seed file by name (e.g. `001_initial_users`):
  ```bash
  ./scripts/migrate.sh seed run --name 001_initial_users
  ```
- Create a new seed template without writing SQL manually:
  ```bash
  ./scripts/migrate.sh seed create add_demo_data
  ```
- Edit the generated SQL to insert/update the rows you need. Each seed runs inside a transaction, so use `INSERT ... ON CONFLICT` if you want it to be idempotent.

### Running Ad-hoc SQL

- Execute inline SQL and see the output directly in your terminal:
  ```bash
  ./scripts/migrate.sh sql --query "SELECT * FROM comments ORDER BY comment_id"
  ```
- Run all statements from a `.sql` file (path can be relative to the repo root):
  ```bash
  ./scripts/migrate.sh sql --file sql/debug_comments.sql
  ```
- Results are printed in a simple table. For non-`SELECT` statements, the affected row count is shown.

### Useful Commands

```bash
# Start DB and apply migrations together
docker compose up db migrator

# Check the current migration version
./scripts/migrate.sh version

# Show applied vs pending migrations
./scripts/migrate.sh status

# Seed sample data
./scripts/migrate.sh seed run

# Run ad-hoc SQL
./scripts/migrate.sh sql --query "SELECT COUNT(*) FROM users"

# Reset the database to a clean state (deletes volume data!)
docker compose down -v
docker compose up -d db
./scripts/migrate.sh up
```
