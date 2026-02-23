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

### Useful Commands

```bash
# Start DB and apply migrations together
docker compose up db migrator

# Check the current migration version
./scripts/migrate.sh version

# Show applied vs pending migrations
./scripts/migrate.sh status

# Reset the database to a clean state (deletes volume data!)
docker compose down -v
docker compose up -d db
./scripts/migrate.sh up
```
