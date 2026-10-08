# Proxy `/api` su Vercel

`vercel.json` inoltra `/api/*` (e sitemap/robots/docs) al backend.

1. Dopo il deploy Render Free, copia l’URL (es. `https://aia-backend-xxxx.onrender.com`).
2. Sostituisci in `vercel.json` ogni host backend con quell’URL (senza slash finale).
3. Commit + push → Vercel ridistribuisce; oppure Redeploy da dashboard.

Guida completa: [`docs/FREE_HOSTING.md`](../docs/FREE_HOSTING.md).
