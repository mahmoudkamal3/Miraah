# Automatic data updates — Mir’ah / مرآة (Miraah)

Mir’ah (English) / مرآة (Arabic) is a static bilingual dashboard. Technical
project spelling: **Miraah**. It does not need an application backend or
database.

## Data flow

- World Bank indicators are refreshed from the official Indicators API v2.
- The updater paginates every indicator response and replaces each indicator
  series only after the full response validates.
- Null API values clear previously stored years for that indicator (no stale
  leftovers). Missing years stay missing — values are never invented or
  forward-filled.
- The date window requested from the API is `2000` through the current UTC
  year, but `DATA.years` is set from `2000` through the latest year that
  actually contains at least one valid numeric observation. Empty current-year
  placeholders are not added.
- The World Happiness Report snapshot remains pinned to the 2026 Figure 2.1
  workbook because the report does not expose the same live API model.
- If any World Bank request fails, pagination is incomplete, or validation
  fails, the script exits without replacing the last known-good dashboard.
- `updatedAt` and `sources.wdi` change only when indicator values or the years
  range actually change.

## Local commands (Windows PowerShell)

From the project root:

```powershell
# Recommended: unit tests
python -m unittest tests.test_update_world_bank -v

# Default mode is dry-run (no files modified)
python scripts/update_world_bank.py

# Explicit dry-run
python scripts/update_world_bank.py --dry-run

# Write updates to public/dashboard.html and public/index.html
# (only after reviewing a successful dry-run summary)
python scripts/update_world_bank.py --write
```

Dry-run and write both print a JSON summary including:

- `indicatorsFetched`, per-indicator `pages`
- `countriesTouched`
- `valuesAdded` / `valuesChanged` / `valuesRemoved`
- `changed`, `wouldWrite`, `wrote`
- `errors` (if any)

When nothing changed, the script prints `"message": "No data changes"` and
exits `0` without touching files.

## GitHub Actions

Workflow: `.github/workflows/update-data.yml` (**Update country data**)

- Schedule: `17 5 1 * *` (05:17 UTC on the 1st of every month)
- Manual: Actions → **Update country data** → **Run workflow**
- Steps:
  1. Unit tests
  2. `python scripts/update_world_bank.py --dry-run`
  3. `python scripts/update_world_bank.py --write`
  4. Verify both HTML files are non-empty, byte-identical, and parseable
  5. Commit + push only when `public/dashboard.html` or `public/index.html`
     actually changed

Enable GitHub Actions with **Read and write permissions** under repository
Settings → Actions → General → Workflow permissions.

## GitHub and Cloudflare Pages

1. Push this project to a GitHub repository.
2. In Cloudflare Pages, connect that repository.
3. For a plain static deployment, set the build output directory to `public`.
4. Alternatively, upload the `public` folder with Direct Upload.
5. A repository-connected Cloudflare Pages project deploys commits from the
   monthly workflow automatically.

Deployment configuration is intentionally unchanged by the updater.
