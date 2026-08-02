# Cloudflare Pages deployment — Mir’ah / مرآة (Miraah)

Mir’ah is a **static** site. Production hosting should serve the contents of the
`public/` directory with **no build step**, no Workers, no Pages Functions, and
no Wrangler deploy from this repository.

## Cloudflare dashboard settings

Use these exact settings when connecting the GitHub repository in Cloudflare Pages:

| Setting | Value |
|---|---|
| Project name | `miraah` |
| Git provider | GitHub |
| Repository | `mahmoudkamal3/Miraah` |
| Production branch | `main` |
| Framework preset | None |
| Build command | leave empty |
| Build output directory | `public` |
| Root directory | leave empty |
| Environment variables | none |

If Cloudflare requires a non-empty build command, use this no-op fallback:

```bash
exit 0
```

Leave **Build output directory** as `public` either way.

Do **not** add Cloudflare API tokens, account IDs, or other credentials to this
repository.

## Automatic deployment flow

1. **Push to `main`** → Cloudflare Pages production deployment of `public/`.
2. **Other branches / pull requests** → Cloudflare Pages preview deployment.
3. **Monthly World Bank update** (GitHub Actions workflow
   `.github/workflows/update-data.yml`) may commit refreshed
   `public/dashboard.html` and `public/index.html` to `main` → that push also
   triggers an automatic Cloudflare production redeployment.

GitHub Actions is responsible **only** for the monthly data refresh. Cloudflare
Pages is responsible for serving the static site after git pushes.

## What is deployed

- Entry point: `public/index.html` (standalone; byte-identical to
  `public/dashboard.html`)
- Assets: HTML, SVG icons under `public/` only
- Runtime data: World Bank + World Happiness Report values are **embedded** in
  the HTML (`const DATA=...`). Normal browsing does not call APIs.
- No Node/npm runtime, database, or backend is required in production.

## Local static check

Serve only the `public` folder:

```powershell
python -m http.server 8080 --directory public
```

Then open `http://127.0.0.1:8080/`.
