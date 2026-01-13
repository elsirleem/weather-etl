#!/usr/bin/env bash
set -euo pipefail

# Simple wrapper to run the weather ETL container.
# Usage:
#   ./run.sh                # uses .env, persists DB, loops with default interval
#   ./run.sh -e RUN_ONCE=true  # single run
#   ./run.sh -e POLL_INTERVAL_SECONDS=300  # override interval

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$ROOT_DIR/data"
ENV_FILE="$ROOT_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env. Copy .env.example to .env and set OPENWEATHER_API_KEY." >&2
  exit 1
fi

mkdir -p "$DATA_DIR"

docker run --rm \
  -v "$DATA_DIR:/app/data" \
  --env-file "$ENV_FILE" \
  weather-etl "$@"
