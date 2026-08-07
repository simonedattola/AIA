# GitHub Actions secrets — AIA Legnano

This document lists the **GitHub repository secrets** required for CI/CD.
Secrets must live only in GitHub (Settings → Secrets and variables → Actions).
**Never commit real values** to the repo, PRs, workflow logs, or issue comments.

Local development uses `.env` / `backend/.env` (see [`.env.example`](../.env.example) and [`backend/.env.example`](../backend/.env.example)).
Those files are gitignored and are **not** the same as GitHub Actions secrets.

---

## How to add secrets

1. Open the repository on GitHub: **Settings → Secrets and variables → Actions**.
2. Click **New repository secret**.
3. Use the **exact name** from the table below (case-sensitive).
4. Paste the value → **Add secret**.

Organization/environment secrets are fine if your org policy requires them; keep the same names.

---

## Required secrets

| Secret name | Purpose | How to generate / obtain |
|-------------|---------|---------------------------|
| `ADMIN_PASSWORD` | Strong password for the seeded admin user used by integration tests / staging seed | `openssl rand -base64 24` (store in a password manager; do not reuse a leaked/historical password) |
| `JWT_SECRET` | HMAC signing key for admin/portal JWTs in CI and deployed backends | `openssl rand -base64 48` (≈256+ bit entropy). Min recommended length: 32 characters |
| `VERCEL_TOKEN` | Authenticates GitHub Actions / CLI deploys to Vercel | Vercel → **Account Settings → Tokens** → create token with deploy scope |
| `VERCEL_ORG_ID` | Vercel team/org scope for CLI (`vercel link` / deploy) | From Vercel project settings or `.vercel/project.json` → `orgId` |
| `VERCEL_PROJECT_ID` | Vercel project id for the **frontend** app | Vercel project → **Settings → General → Project ID**. Alias name used in docs historically: `VERCEL_PROJECT_ID_FRONTEND` — prefer `VERCEL_PROJECT_ID` for Vercel’s official CLI env vars; if you already created `VERCEL_PROJECT_ID_FRONTEND`, map it in workflows with `VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID_FRONTEND }}` |
| `MONGO_TEST_URL` | MongoDB connection string for CI integration tests | Dedicated throwaway/test cluster or container, e.g. `mongodb://localhost:27017` in a CI service container, or Atlas URI with a **test-only** database. Do **not** point at production |

### Optional secrets

| Secret name | Purpose | Notes |
|-------------|---------|--------|
| `DOCKER_USERNAME` | Docker Hub (or registry) username for image push | Optional until image publishing is enabled |
| `DOCKER_PASSWORD` | Docker Hub access token / password | Prefer an **access token**, not the account password |
| `ADMIN_EMAIL` | Admin email for CI seed/login | Defaults to `admin@aia-legnano.it` in code if unset; set explicitly in CI for clarity |
| `REACT_APP_BACKEND_URL` | Backend base URL for frontend build/tests | e.g. staging API URL; not strictly a “secret” but often stored as a variable |

---

## Mapping to workflows

Workflows should reference secrets only via expressions, for example:

```yaml
env:
  ADMIN_EMAIL: ${{ secrets.ADMIN_EMAIL }}
  ADMIN_PASSWORD: ${{ secrets.ADMIN_PASSWORD }}
  JWT_SECRET: ${{ secrets.JWT_SECRET }}
  MONGO_URL: ${{ secrets.MONGO_TEST_URL }}
  VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
  VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

Never echo these values. Prefer `::add-mask::` if a step must print a derived string that might contain a secret.

---

## Checklist (acceptance)

- [ ] `ADMIN_PASSWORD` set in GitHub Actions secrets
- [ ] `JWT_SECRET` set (long random; not a placeholder like `change-me`)
- [ ] `VERCEL_TOKEN` set
- [ ] `VERCEL_ORG_ID` set
- [ ] `VERCEL_PROJECT_ID` (or `VERCEL_PROJECT_ID_FRONTEND` + workflow mapping) set
- [ ] `MONGO_TEST_URL` set to a **non-production** database
- [ ] `DOCKER_USERNAME` / `DOCKER_PASSWORD` set only if Docker image publish is required
- [ ] Repo scan: no real passwords/JWTs in `docker-compose.yml`, source, or committed reports
- [ ] Local `.env` files remain untracked

---

## Rotation policy

Rotate immediately if a secret is exposed (commit, screenshot, CI log, shared chat). Otherwise rotate on this cadence:

| Secret | Suggested rotation |
|--------|--------------------|
| `JWT_SECRET` | Every 90 days, or on suspected leak. **Effect:** invalidates existing JWTs (users must log in again). Update GitHub secret + every deployed environment’s env vars together |
| `ADMIN_PASSWORD` | Every 90 days, or on suspected leak. Update GitHub secret + runtime env; restart/redeploy so seed/`ADMIN_PASSWORD` sync applies |
| `VERCEL_TOKEN` | On member offboarding, or yearly. Revoke old token in Vercel UI, create a new one, update the GitHub secret |
| `MONGO_TEST_URL` | When credentials change or cluster is rebuilt. Rotate DB user password in Atlas/host, then update the secret |
| `DOCKER_PASSWORD` | On member offboarding, or yearly. Revoke Docker Hub token, create a new one |

### Rotation steps (generic)

1. Generate a new value (`openssl rand …` or provider UI).
2. Update the secret in **GitHub → Settings → Secrets and variables → Actions** (same name, new value).
3. Update the same value in every runtime environment that needs it (Vercel env, Docker host `.env`, staging VM, etc.).
4. Redeploy / restart services that read the secret at boot.
5. For `JWT_SECRET` / `ADMIN_PASSWORD`, verify login against staging before production.
6. Revoke/delete the **old** token/password at the provider when applicable (Vercel, Docker Hub, Atlas).
7. Record the rotation date in your internal ops log (not in this repo).

---

## Zero secrets in code

Allowed in git:

- Placeholder templates: `.env.example`, `backend/.env.example`
- This documentation
- Workflow files that only reference `${{ secrets.NAME }}`

Not allowed:

- Real passwords, JWTs, tokens, or connection strings with credentials
- Default fallbacks in application code that embed production-like passwords

If git history still contains an old password, **rotate** that credential even after removing it from `HEAD`.
