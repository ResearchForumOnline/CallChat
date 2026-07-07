#!/usr/bin/env bash
set -euo pipefail

# Public template only. Review paths before using.

STAMP="$(date -u +%Y%m%d-%H%M%S)"
OUT_DIR="${1:-./backups/callchat-$STAMP}"
COMPOSE_DIR="${COMPOSE_DIR:-./infra/synapse}"

mkdir -p "$OUT_DIR"

echo "Creating Synapse/PostgreSQL backup template output in $OUT_DIR"
echo "This script does not know your production paths. Review before use."

(
  cd "$COMPOSE_DIR"
  docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-synapse}" "${POSTGRES_DB:-synapse}" > "$OLDPWD/$OUT_DIR/postgres.sql"
)

echo "Database dump written to $OUT_DIR/postgres.sql"
echo "Now separately copy Synapse config, signing keys, media store, reverse proxy config, and .well-known files into private encrypted storage."
