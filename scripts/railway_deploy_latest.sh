#!/usr/bin/env bash
# Deploy latest backend to Railway (fresh build from origin/main).
# Auth: /home/ubuntu/.config/railway-aia.env (RAILWAY_TOKEN, RAILWAY_SERVICE=AIA)
# IMPORTANT: upload from REPO ROOT — service Root Directory is /backend.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECRETS="${RAILWAY_SECRETS_FILE:-/home/ubuntu/.config/railway-aia.env}"

if [[ -f "$SECRETS" ]]; then
  # shellcheck disable=SC1090
  set -a; source "$SECRETS"; set +a
fi

if [[ -z "${RAILWAY_TOKEN:-}" ]]; then
  echo "Missing RAILWAY_TOKEN" >&2
  exit 2
fi

SERVICE="${RAILWAY_SERVICE:-AIA}"

git -C "$ROOT" fetch origin main
git -C "$ROOT" checkout main
git -C "$ROOT" pull --ff-only origin main

echo "Deploying repo root → service=$SERVICE (Root Directory=/backend)…"
cd "$ROOT"
npx --yes @railway/cli up --ci --detach -y --service "$SERVICE"
echo "Triggered. Poll: curl -sS https://aia-production-00a9.up.railway.app/api/cron/designations-sync"
