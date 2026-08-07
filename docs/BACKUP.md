# Backup & Disaster Recovery

This document describes how to back up and restore the AIA Legnano platform data
(MongoDB) and uploaded media.

## What to back up

| Asset | Location | Notes |
|-------|----------|--------|
| MongoDB database | `DB_NAME` (default `aia_legnano`) | CMS pages, articles, members, designations, portal data |
| Uploads | `backend/uploads/` (or `UPLOAD_DIR`) | Images, PDFs, gallery files served under `/api/uploads` |
| Secrets | `.env` / host secret store | **Never** commit; store in a password manager / vault |

## MongoDB backup (local / self-hosted)

### Dump

```bash
mkdir -p ./backups
mongodump --uri "mongodb://localhost:27017" --db aia_legnano --out "./backups/mongo-$(date +%Y%m%d)"
```

With authentication:

```bash
mongodump --uri "mongodb://USER:PASS@localhost:27017/aia_legnano?authSource=admin" \
  --out "./backups/mongo-$(date +%Y%m%d)"
```

### Restore

```bash
mongorestore --uri "mongodb://localhost:27017" --db aia_legnano \
  --drop "./backups/mongo-<YYYYMMDD>/aia_legnano"
```

`--drop` replaces existing collections; omit it to merge (may create duplicates).

### Verify

```bash
mongosh --quiet mongodb://localhost:27017/aia_legnano --eval 'db.getCollectionNames()'
mongosh --quiet mongodb://localhost:27017/aia_legnano --eval 'db.articles.countDocuments({})'
```

## Uploads backup (local filesystem)

```bash
tar -czf "./backups/uploads-$(date +%Y%m%d).tar.gz" -C backend uploads
```

Restore:

```bash
tar -xzf "./backups/uploads-<YYYYMMDD>.tar.gz" -C backend
```

## Daily snapshot via cron (example)

```cron
# Daily 02:15 — Mongo dump + uploads tarball, keep 14 days
15 2 * * * cd /opt/aia && mkdir -p backups && mongodump --uri "$MONGO_URL" --db aia_legnano --out "backups/mongo-$(date +\%Y\%m%d)" && tar -czf "backups/uploads-$(date +\%Y\%m%d).tar.gz" -C backend uploads && find backups -mtime +14 -delete
```

Store cron output / dump directories on a volume that is itself snapshotted.

## Production strategy (recommended)

1. **MongoDB Atlas** (or equivalent managed Mongo) with **automated backups / PITR** enabled.
2. **Object storage for uploads** (AWS S3, Cloudflare R2, GCS) instead of local disk — versioning + lifecycle rules.
3. **Application secrets** in the host secret manager (GitHub Actions secrets, Vercel/env vault) — rotate after any restore that might expose old credentials.
4. **Regular restore drills** (at least quarterly): restore a dump into a staging DB and smoke-test `/api/health`, admin login, and one public page.
5. **Retention**: keep ≥ 7 daily + 4 weekly backups (adjust to policy).

## Disaster recovery checklist

1. Provision Mongo (Atlas or local) and set `MONGO_URL` / `DB_NAME`.
2. Restore DB with `mongorestore` (or Atlas restore UI).
3. Restore uploads to `UPLOAD_DIR` or re-point the app at the S3 bucket.
4. Set `JWT_SECRET`, `ADMIN_PASSWORD`, CORS, and `PUBLIC_API_URL`.
5. Start API → confirm `GET /api/health` returns `database: connected`.
6. Log in to `/admin` and open a member profile + one article with images.

## Production object storage (AWS S3 / Cloudflare R2)

Local `UPLOAD_DIR` is the default. For production, set:

```bash
STORAGE_BACKEND=s3
S3_BUCKET=aia-legnano-uploads
S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com   # omit for AWS S3
S3_REGION=auto                    # or eu-west-1, etc.
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_PREFIX=uploads                 # optional key prefix
S3_PUBLIC_BASE_URL=https://cdn.example.com   # CloudFront / R2 custom domain
```

See `app/paths.py` and `app/storage.py`. With `S3_PUBLIC_BASE_URL`, media URLs resolve to the CDN; without it the API streams/redirects from `/api/uploads/{name}`.

### Migrating existing files to the bucket

```bash
# Example: sync local uploads into an S3/R2 bucket (AWS CLI / rclone)
aws s3 sync backend/uploads/ s3://aia-legnano-uploads/uploads/ \
  --endpoint-url "$S3_ENDPOINT_URL"
```

Then point the app at object storage (`STORAGE_BACKEND=s3`) and keep a final local tarball for rollback.

### Backing up a bucket

Prefer **bucket versioning + lifecycle rules**. Periodic inventory copy:

```bash
aws s3 sync s3://aia-legnano-uploads ./backups/s3-$(date +%Y%m%d) \
  --endpoint-url "$S3_ENDPOINT_URL"
```

## Indexes after restore

On startup the API runs `app.db_indexes.create_indexes()` (idempotent).  
You can also run manually from a Python shell:

```python
import asyncio
from app.db_indexes import create_indexes
asyncio.run(create_indexes())
```

## Related

- Health probe: `GET /api/health`
- Index definitions: `backend/app/db_indexes.py`
