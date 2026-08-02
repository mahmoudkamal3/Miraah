# Cloudflare Workers Static Assets deployment — Mir’ah / مرآة (Miraah)

Mir’ah is deployed as a **static-assets-only** Cloudflare Worker project using
Git integration (Workers Builds). There is no Worker entry point, backend,
database, bindings, environment variables, or secrets.

Production assets live in `public/` and are declared in `wrangler.jsonc`.

## Cloudflare Workers Builds dashboard settings

| Setting | Value |
|---|---|
| Repository | `mahmoudkamal3/Miraah` |
| Project name | `miraah` |
| Production branch | `main` |
| Build command | leave empty |
| Deploy command | `npx wrangler deploy` |
| Root directory | leave empty |
| Non-production branch builds | enabled |
| Environment variables | none |

Do **not** use `npm run build` for production deployment.

If the dashboard insists on a non-empty build command, use:

```bash
exit 0
```

The deploy command must remain:

```bash
npx wrangler deploy
```

Do **not** add Cloudflare API tokens, account IDs, or other credentials to this
repository.

## Wrangler config

`wrangler.jsonc` at the repository root:

```jsonc
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "miraah",
  "compatibility_date": "2026-08-02",
  "assets": {
    "directory": "./public"
  }
}
```

`wrangler` is listed in `package.json` / `package-lock.json` (devDependency).

## Automatic deployment flow

1. **Push to `main`** → Workers Builds runs deploy (`npx wrangler deploy`) →
   production.
2. **Other branches / PRs** → non-production branch builds / preview deployments
   (enabled).
3. **Monthly World Bank update** (`.github/workflows/update-data.yml`) may commit
   refreshed `public/dashboard.html` and `public/index.html` to `main` → that
   push also triggers an automatic Cloudflare redeployment.

GitHub Actions remains responsible **only** for monthly World Bank data
updates. Cloudflare Workers Builds handles deployment after git pushes.

## What is deployed

- Entry point: `public/index.html` (standalone; byte-identical to
  `public/dashboard.html`)
- Assets: HTML and SVG files under `public/` only
- Runtime data: World Bank + World Happiness Report values are **embedded** in
  the HTML (`const DATA=...`). Normal browsing does not call APIs.
- No Node/npm application runtime, database, or backend in production.

## Local checks

```powershell
# Config dry-run (no Cloudflare auth / no real deploy)
npx wrangler deploy --dry-run

# Optional: serve public/ directly
python -m http.server 8080 --directory public
```
