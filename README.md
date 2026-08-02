# Mir’ah / مرآة (Miraah)

**Mir’ah** (English) / **مرآة** (Arabic) is a bilingual country comparison
dashboard. The technical project name is **Miraah**.

Compare countries through data — quality of life, economy, and happiness — using
World Bank indicators and a pinned World Happiness Report snapshot.

## Brand

| Language | Display name | Tagline |
|---|---|---|
| English | Mir’ah | Compare countries through data |
| Arabic | مرآة | قارن الدول بالأرقام |

Technical / repository / package spelling: `miraah`

## Prerequisites

- Node.js `>=22.13.0`
- Python 3.12+ (for World Bank data refresh scripts)

## Local development (Windows PowerShell)

```powershell
npm install
$env:WRANGLER_LOG_PATH=".wrangler/wrangler.log"; npx vite
```

Open the local Vite URL. The comparison UI is served from
`public/dashboard.html` (also mirrored as `public/index.html`).

## Data updates

World Bank WDI series can be refreshed safely with dry-run by default:

```powershell
python -m unittest tests.test_update_world_bank -v
python scripts/update_world_bank.py --dry-run
python scripts/update_world_bank.py --write
```

See [AUTOMATIC_UPDATES.md](AUTOMATIC_UPDATES.md) for the monthly GitHub Actions
workflow, pagination rules, and observation-based `DATA.years` behavior.

## Project shape

- `scripts/render_dashboard.py` — bilingual UI shell around embedded `DATA`
- `scripts/update_world_bank.py` — World Bank refresher (`User-Agent: Miraah/1.0`)
- `public/dashboard.html` / `public/index.html` — generated static dashboards
- `app/` — Next/vinext shell that iframes the dashboard
- `tests/` — updater unit tests and rendered-html checks

## Sites / vinext notes

This checkout can also run under
[vinext](https://github.com/cloudflare/vinext). Scripts that need writable
project-scoped home, npm, XDG, and temporary paths use `scripts/sites-env.sh`.
Generated `.sites-runtime/`, `.wrangler/`, and `node_modules/` are gitignored.
