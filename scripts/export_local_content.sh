#!/usr/bin/env bash
# Export local MongoDB + uploads for go-live / restore on Atlas or another host.
# Usage: ./scripts/export_local_content.sh [outdir]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/backups/local-export-$(date +%Y%m%d-%H%M%S)}"
DB_NAME="${DB_NAME:-aia_legnano}"
MONGO_URL="${MONGO_URL:-mongodb://127.0.0.1:27017}"

mkdir -p "$OUT"
echo "Exporting MongoDB '$DB_NAME' → $OUT/mongo"
if command -v mongodump >/dev/null 2>&1; then
  mongodump --uri="$MONGO_URL" --db="$DB_NAME" --out="$OUT/mongo"
else
  echo "mongodump not found; writing JSON collections via pymongo"
  python3 - <<PY
from pymongo import MongoClient
import json, os
from bson import json_util
out = os.path.join("$OUT", "mongo", "$DB_NAME")
os.makedirs(out, exist_ok=True)
db = MongoClient("$MONGO_URL")["$DB_NAME"]
for name in db.list_collection_names():
    path = os.path.join(out, f"{name}.json")
    docs = list(db[name].find({}, {"_id": 0}))
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(docs, ensure_ascii=False, indent=2))
    print(name, len(docs))
PY
fi

UPLOADS_SRC="$ROOT/backend/uploads"
if [ -d "$UPLOADS_SRC" ]; then
  echo "Copying uploads → $OUT/uploads"
  mkdir -p "$OUT/uploads"
  # Exclude huge media if needed; copy all by default
  cp -a "$UPLOADS_SRC"/. "$OUT/uploads/" || true
fi

python3 - <<PY
import json, os
from pathlib import Path
out = Path("$OUT")
manifest = {
  "db_name": "$DB_NAME",
  "mongo_path": "mongo",
  "uploads_path": "uploads",
  "created_by": "scripts/export_local_content.sh",
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("Wrote", out / "manifest.json")
PY

echo "Done: $OUT"
du -sh "$OUT" "$OUT/uploads" 2>/dev/null || true
