#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$ROOT/runtime"
ENV_FILE="$ROOT/infra/synapse/.env"
WEBROOT_DEFAULT="/var/www/callchat.org/public"

usage() {
  cat <<'MSG'
CallChat Community control script

Commands:
  wizard                         Interactive config builder
  write-env DOMAIN MATRIX_URL    Write infra/synapse/.env and web discovery files
  start-stack                    Start Synapse/PostgreSQL with Docker Compose
  stop-stack                     Stop the Docker Compose stack
  install-element [VERSION]      Download Element Web and write CallChat config
  install-openzero               Run the public OpenZero installer hook
  install-widget WEBROOT         Copy CallChat site agent widget into a webroot
  status [PUBLIC_URL MATRIX_URL] Check public discovery and Matrix API
  backup-web WEBROOT             Create a tar.gz backup of a webroot

Examples:
  bash scripts/callchatctl.sh wizard
  bash scripts/callchatctl.sh write-env example.com https://matrix.example.com
  bash scripts/callchatctl.sh install-widget /var/www/example.com/public
MSG
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

safe_domain() {
  case "$1" in
    *[!A-Za-z0-9.-]*|""|.*|*..*|*.) return 1 ;;
    *) return 0 ;;
  esac
}

write_env() {
  local domain="$1"
  local matrix_url="$2"
  safe_domain "$domain" || { echo "Invalid public domain: $domain" >&2; exit 1; }
  case "$matrix_url" in
    https://*) ;;
    *) echo "Matrix URL must start with https://" >&2; exit 1 ;;
  esac

  mkdir -p "$ROOT/infra/synapse" "$ROOT/web/public/.well-known/matrix"
  local db_pass turn_secret
  db_pass="$(openssl rand -hex 24 2>/dev/null || date +%s%N)"
  turn_secret="$(openssl rand -hex 24 2>/dev/null || date +%s%N)"

  cat > "$ENV_FILE" <<EOF
SERVER_NAME=$domain
PUBLIC_BASEURL=$matrix_url/
SYNAPSE_REPORT_STATS=no

POSTGRES_DB=synapse
POSTGRES_USER=synapse
POSTGRES_PASSWORD=$db_pass

SYNAPSE_CONFIG_PATH=/data/homeserver.yaml
SYNAPSE_DATA_PATH=/data

TURN_URIS=
TURN_SHARED_SECRET=$turn_secret
TURN_USER_LIFETIME=86400000
EOF

  cat > "$ROOT/web/public/.well-known/matrix/client" <<EOF
{
  "m.homeserver": {
    "base_url": "$matrix_url"
  }
}
EOF

  local matrix_host
  matrix_host="${matrix_url#https://}"
  cat > "$ROOT/web/public/.well-known/matrix/server" <<EOF
{
  "m.server": "$matrix_host:443"
}
EOF

  echo "Wrote $ENV_FILE"
  echo "Wrote Matrix discovery JSON for $domain -> $matrix_url"
  echo "Do not commit infra/synapse/.env."
}

wizard() {
  echo "CallChat Community setup wizard"
  echo
  read -r -p "Public domain [callchat.example.com]: " public_domain
  public_domain="${public_domain:-callchat.example.com}"
  read -r -p "Matrix API URL [https://matrix.$public_domain]: " matrix_url
  matrix_url="${matrix_url:-https://matrix.$public_domain}"
  write_env "$public_domain" "$matrix_url"
  write_element_config "$public_domain" "$matrix_url"
  echo
  echo "Next:"
  echo "  bash scripts/callchatctl.sh install-element"
  echo "  bash scripts/callchatctl.sh start-stack"
  echo "  bash scripts/callchatctl.sh status https://$public_domain $matrix_url"
}

start_stack() {
  need_cmd docker
  (cd "$ROOT/infra/synapse" && docker compose up -d)
}

stop_stack() {
  need_cmd docker
  (cd "$ROOT/infra/synapse" && docker compose down)
}

latest_element_version() {
  need_cmd curl
  python3 - <<'PY' 2>/dev/null || true
import json, urllib.request
with urllib.request.urlopen("https://api.github.com/repos/element-hq/element-web/releases/latest", timeout=20) as r:
    print(json.load(r)["tag_name"].lstrip("v"))
PY
}

write_element_config() {
  local public_domain="$1"
  local matrix_url="$2"
  mkdir -p "$RUNTIME/element-web"
  sed \
    -e "s#https://matrix.example.com#$matrix_url#g" \
    -e "s#example.com#$public_domain#g" \
    "$ROOT/element/config.sample.json" > "$RUNTIME/element-web/config.json"
  echo "Wrote $RUNTIME/element-web/config.json"
}

install_element() {
  need_cmd curl
  need_cmd tar
  local version="${1:-${ELEMENT_VERSION:-}}"
  if [ -z "$version" ]; then
    version="$(latest_element_version)"
  fi
  if [ -z "$version" ]; then
    echo "Could not detect latest Element Web version. Set ELEMENT_VERSION and retry." >&2
    exit 1
  fi
  mkdir -p "$RUNTIME/downloads" "$RUNTIME/element-web"
  local archive="$RUNTIME/downloads/element-v$version.tar.gz"
  local url="https://github.com/element-hq/element-web/releases/download/v$version/element-v$version.tar.gz"
  local existing_config=""
  if [ -f "$RUNTIME/element-web/config.json" ]; then
    existing_config="$RUNTIME/downloads/config-before-element-install.json"
    cp "$RUNTIME/element-web/config.json" "$existing_config"
  fi
  echo "Downloading Element Web v$version"
  curl -fL "$url" -o "$archive"
  rm -rf "$RUNTIME/element-web"
  mkdir -p "$RUNTIME/element-web"
  tar -xzf "$archive" --strip-components=1 -C "$RUNTIME/element-web"
  if [ -n "$existing_config" ] && [ -f "$existing_config" ]; then
    cp "$existing_config" "$RUNTIME/element-web/config.json"
  elif [ -f "$RUNTIME/element-web/config.sample.json" ] && [ ! -f "$RUNTIME/element-web/config.json" ]; then
    cp "$ROOT/element/config.sample.json" "$RUNTIME/element-web/config.json"
  fi
  mkdir -p "$RUNTIME/element-web/callchat-theme"
  cp "$ROOT/element/theme/callchat-theme.css" "$RUNTIME/element-web/callchat-theme/"
  echo "Element Web installed to $RUNTIME/element-web"
}

install_openzero() {
  need_cmd curl
  echo "OpenZero installer will run from the public OpenZero project."
  echo "Review first: https://raw.githubusercontent.com/ResearchForumOnline/OpenZero/main/openzero/install.sh"
  read -r -p "Run OpenZero installer now? [y/N]: " answer
  case "$answer" in
    y|Y|yes|YES)
      curl -fsSL https://raw.githubusercontent.com/ResearchForumOnline/OpenZero/main/openzero/install.sh | bash
      ;;
    *)
      echo "Skipped OpenZero install."
      ;;
  esac
}

backup_web() {
  local webroot="${1:-$WEBROOT_DEFAULT}"
  [ -d "$webroot" ] || { echo "Webroot not found: $webroot" >&2; exit 1; }
  local stamp out
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  out="$ROOT/backups/webroot-$stamp.tgz"
  mkdir -p "$ROOT/backups"
  tar -czf "$out" -C "$webroot" .
  echo "$out"
}

install_widget() {
  need_cmd python3
  local webroot="${1:?Usage: callchatctl install-widget /path/to/webroot}"
  [ -d "$webroot" ] || { echo "Webroot not found: $webroot" >&2; exit 1; }
  local backup
  backup="$(backup_web "$webroot")"
  mkdir -p "$webroot/assets/callchat-widget"
  cp "$ROOT/widgets/zero-agent-widget/zero-agent-widget.js" "$webroot/assets/callchat-widget/"
  cp "$ROOT/widgets/zero-agent-widget/zero-agent-widget.css" "$webroot/assets/callchat-widget/"
  if [ -f "$webroot/index.html" ] && ! grep -q "callchat-zero-agent-widget" "$webroot/index.html"; then
    python3 "$ROOT/widgets/zero-agent-widget/inject_widget.py" "$webroot/index.html" "/assets/callchat-widget/zero-agent-widget.js" "/assets/callchat-widget/zero-agent-widget.css"
  fi
  echo "Widget installed. Backup: $backup"
}

status() {
  local public_url="${1:-https://example.com}"
  local matrix_url="${2:-https://matrix.example.com}"
  "$ROOT/scripts/healthcheck.sh" "$public_url" "$matrix_url"
}

cmd="${1:-wizard}"
shift || true
case "$cmd" in
  wizard) wizard "$@" ;;
  write-env) write_env "$@" ;;
  start-stack) start_stack "$@" ;;
  stop-stack) stop_stack "$@" ;;
  install-element) install_element "$@" ;;
  install-openzero) install_openzero "$@" ;;
  install-widget) install_widget "$@" ;;
  backup-web) backup_web "$@" ;;
  status) status "$@" ;;
  -h|--help|help) usage ;;
  *) usage; exit 1 ;;
esac
