#!/usr/bin/env bash
set -euo pipefail

for forbidden in \
  element/zmath-auto \
  web/public/shield/app \
  zmath-private \
  shield-private \
  entitlement-private \
  docs/private-cryptography; do
  if test -e "$forbidden"; then
    echo "Private or licensed implementation path must not be public: $forbidden" >&2
    exit 1
  fi
done

if git ls-files | grep -E '(^|/)(\.env|private|secrets|backups)(/|$)|\.(key|pem|p12|pfx|jks|sqlite|db|bak|old|tgz|zip)$' \
  | grep -vE '(^|/)\.env\.example$|example\.env$'; then
  echo "A tracked path violates the public disclosure boundary." >&2
  exit 1
fi

if git grep -n -I -E 'ionq_submit_factor_job|ionq_factor_job|IONQ_FACTOR_DOMAIN|measurement_sha512|ZMath-Auto-Recovery|ZMATH-PBKDF2-HKDF-AESGCM' \
  -- . ':!scripts/check-public-boundary.sh'; then
  echo "Implementation-level premium material violates the public disclosure boundary." >&2
  exit 1
fi

echo "CallChat public disclosure boundary: ok"
