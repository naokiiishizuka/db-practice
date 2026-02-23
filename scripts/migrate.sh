#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ $# -lt 1 ]]; then
  cat <<'USAGE' >&2
Usage: ./scripts/migrate.sh <command> [args...]

Commands:
  up [--target VERSION]
  down [steps]
  status
  version
  create <name>
  seed run [--name id]
  seed create <name>
  sql (--query "SQL" | --file path/to.sql | --name preset)
USAGE
  exit 1
fi

CMD="$1"
shift || true

REQUIRES_ENV=true
if [[ "${CMD}" == "create" ]]; then
  REQUIRES_ENV=false
elif [[ "${CMD}" == "seed" && "${1:-}" == "create" ]]; then
  REQUIRES_ENV=false
fi

if [[ "${REQUIRES_ENV}" == true && ! -f ".env" ]]; then
  echo "Missing .env file. Copy .env.example to .env first." >&2
  exit 1
fi

if [[ "${CMD}" == "create" ]]; then
  docker compose run --rm --no-deps migrator create "$@"
elif [[ "${CMD}" == "seed" && "${1:-}" == "create" ]]; then
  docker compose run --rm --no-deps migrator seed "$@"
else
  docker compose run --rm migrator "${CMD}" "$@"
fi
