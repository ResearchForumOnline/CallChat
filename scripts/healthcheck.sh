#!/usr/bin/env bash
set -euo pipefail

PUBLIC_URL="${1:-https://example.com}"
MATRIX_URL="${2:-https://matrix.example.com}"

failures=0

check_url() {
  local url="$1"
  printf 'Checking %s ... ' "$url"
  if curl -fsS --max-time 15 "$url" >/dev/null; then
    echo "ok"
  else
    echo "failed"
    failures=$((failures + 1))
  fi
}

check_url "$PUBLIC_URL/.well-known/matrix/client"
check_url "$PUBLIC_URL/.well-known/matrix/server"
check_url "$MATRIX_URL/_matrix/client/versions"

if [ "$failures" -gt 0 ]; then
  echo "$failures check(s) failed"
  exit 1
fi

echo "All public health checks passed"
