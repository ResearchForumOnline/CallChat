#!/usr/bin/env bash
set -euo pipefail

cat <<'MSG'
CallChat Community install helper

This helper is intentionally conservative. It does not install Docker, edit your
web server, or request secrets. Read docs/install.md first.

Next manual steps:
1. Copy infra/synapse/.env.example to infra/synapse/.env
2. Set your final SERVER_NAME and Matrix API URL
3. Generate Synapse config with docker compose
4. Configure Apache or Nginx reverse proxy
5. Deploy web/public to your public web root
6. Run scripts/healthcheck.sh
MSG
