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
USAGE
  exit 1
fi

CMD="$1"
shift || true

if [[ "${CMD}" != "create" && ! -f ".env" ]]; then
  echo "Missing .env file. Copy .env.example to .env first." >&2
  exit 1
fi

if [[ "${CMD}" == "create" ]]; then
  docker compose run --rm --no-deps migrator create "$@"
else
  docker compose run --rm migrator "${CMD}" "$@"
fi
