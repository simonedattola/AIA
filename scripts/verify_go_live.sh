#!/usr/bin/env bash
# Smoke test after DNS cutover or Vercel preview.
# Usage: ./scripts/verify_go_live.sh [BASE_URL]
# Example: ./scripts/verify_go_live.sh https://www.aia-legnano.it

set -euo pipefail

BASE="${1:-https://www.aia-legnano.it}"
BASE="${BASE%/}"

echo "== Go-live check: $BASE =="

check_json() {
  local path="$1"
  local label="$2"
  echo -n "  $label ... "
  body="$(curl -fsS "$BASE$path" 2>/dev/null)" || {
    echo "FAIL (HTTP/curl)"
    return 1
  }
  if echo "$body" | grep -q '"status"'; then
    echo "OK"
  elif echo "$body" | grep -qi '<html'; then
    echo "FAIL (got HTML, expected JSON — proxy /api missing?)"
    return 1
  else
    echo "OK (response)"
  fi
}

check_html() {
  local path="$1"
  local label="$2"
  echo -n "  $label ... "
  code="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE$path")"
  if [[ "$code" == "200" ]]; then
    echo "OK ($code)"
  else
    echo "FAIL (HTTP $code)"
    return 1
  fi
}

check_json "/api/health" "API health"
check_json "/api/public/settings" "Public settings"
check_html "/" "Homepage SPA"
check_html "/brand/logo-aia-legnano-email.png" "Logo statico"

echo "== Done =="
