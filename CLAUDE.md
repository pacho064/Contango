# Contango Energy

Middle East crude + AI compute intelligence site. Pure HTML/CSS/JS on GitHub Pages, GitHub Actions automation. Owner is non-technical: give exact find-and-replace edits, explain the purpose first, prefer surgical edits over rewrites.

## Editorial rule (governs content AND automation)
Verifiable facts only, with named sources and dates. No opinions or forecasts attributed to Contango. Scripts must never invent, infer, or blend numbers from different dates.

## Structure
- 12 primary pages (in every page's nav, this order): index, saudi-arabia, iraq, buyer-exposure, spare-capacity, opec-compliance, osp-decoder, grades, commodities, natural-gas, ai-compute, compute-atlas.
- Secondary pages: methodology, about, sources, roadmap (about/sources/roadmap have their own small nav).
- Canonical domain is contango-energy.com, never pacho064.github.io.
- Every page: sticky nav + Dark/Light toggle (theme in localStorage), `body{animation:fadeIn .25s ease-in}`, footer with sources + "Not financial advice".
- When adding a primary page: add it to the nav on ALL pages, to sitemap.xml, and to the index quick links.

## Data and automation
- `data/prices.json` — written weekdays 18:00 UTC by `updater.py` (EIA: Brent, WTI, Saudi/Iraq production, SPR). Appends `data/history/crude-daily.jsonl`.
- `data/events.json` — written daily 06:00 UTC by `news_update.py` (GDELT -> Claude Haiku extraction). Fields are `hl` and `src`; JS also accepts `text`/`headline` and `source`.
- `data/compute-assets.json` — hand-maintained AI compute assets (33). `timeline` fields drive `getStatusAtYear()`.
- `data/live.json` — written on weekdays by `live_update.py` (workflow `update-live.yml`, OilPriceAPI free tier, 50 calls/day budget). Brent + WTI every 30 min (1 call). Regional grades (Dubai, OPEC basket, WCS, plus any in `EXTRA_CODES`) every 4 hours (1 call) — these move at business-day cadence. About 38 calls/day. Shown on the homepage: Brent/WTI as a "Live" line under the EIA tiles, regional grades in the "Regional crude grades" table (hidden until data exists). Every figure carries the API's own timestamp and source label. `synthetic` values are never published; `stale` values are hidden. The page re-checks live.json every 60 s while visible (`refreshLive`).
  - Regional values are reference prices, NOT Platts/Argus assessments and NOT official selling prices; real-time Dubai/Oman/Murban/Basrah do not exist on any free source. Keep that caveat on the page.
  - A code the API rejects (unknown or not on the plan) is remembered in `live.json` under `regional_unavailable` and skipped. `--retry-unavailable` re-tries them (e.g. after a plan change).
  - Commands: `OILPRICEAPI_KEY=... python3 live_update.py --all` (local test, forces regional), `--list-codes` (find codes for Urals, Bonny Light, Mars...), `EXTRA_CODES="CODE=Label,..."` to add grades without editing code.
  - Values from the API are put on the page with `textContent` only, never `innerHTML`. Keep it that way.
- `data/chokepoints-live.json` — written daily by `portwatch_update.py` (workflow `update-portwatch.yml`, IMF PortWatch ArcGIS feature service, free, no key). Strait of Hormuz only (portid `chokepoint6`; the script refuses to publish if that id's name stops containing "Hormuz"). Latest day, 60-day series, plus a plain 7-day mean and the same 7 days a year earlier (null if any day is missing). PortWatch runs several days behind, so the page always shows the data date. Shown in the "Strait of Hormuz · vessel transits" section on the homepage (hidden until data exists). Counts are vessels, not barrels, and are a different series from the Lloyd's List item in the static chokepoint cards.
- `data/gas-storage.json` — written daily by `gie_update.py` (workflow `update-gas.yml`, GIE AGSI, free personal key in `GIE_API_KEY`, sent as `x-key`). EU aggregate: fill %, TWh, injection/withdrawal, point difference vs same day last year and vs the mean of the prior five years (computed from GIE's own values, null if a day is missing). Shown at the top of the storage section on natural-gas.html; the July 2026 block under it is a dated snapshot.
  - Both scripts were written from documented field names and tested against a fake server only (the build sandbox cannot reach either host). First real run: trigger each workflow from the Actions tab and read the log; if a field name differs, fix the parser, not the page.
- `osp_update.py` — run by hand monthly with OSP differentials.
- Secrets: `EIA_API_KEY`, `ANTHROPIC_API_KEY`, `OILPRICEAPI_KEY`, `GIE_API_KEY`.
- Homepage tiles are labelled "(EIA spot)" because that is what they are (Europe Brent / Cushing WTI spot, lagged about a week). They were previously mislabelled "ICE Brent".

## Rendering pattern
Render from fallback data first, then fetch live JSON silently and re-render. Never leave "Loading…" or "—" as a resting state. Guard any Chart.js call with try/catch so a blocked CDN cannot stop data from rendering (fixed on index and saudi-arabia; keep it that way).

## How to verify a change (important)
Do NOT judge rendering by fetching the HTML as text: the values are filled in by JavaScript, so a plain fetch shows "—" even when the site works. Load the page in a real browser or headless Chrome and read the rendered text. GitHub Pages caches hard: hard-refresh (Cmd+Shift+R) before concluding something is broken.

## Gotchas
- A `let` declared twice is a silent SyntaxError that kills the whole page script.
- Tab views that overlap: use `position:absolute;inset:0` + `display:block`, not `display:flex`.
- Never put `JSON.stringify()` in an onclick attribute; use `data-id` plus a lookup function.
- Init MapLibre (or any CDN library) inside `window.addEventListener('load', ...)`.
- Claude's artifact preview blocks CDNs; test maps on the deployed site.

## Known open issues (verified Nov 2026)
1. OSP spread mixes dates: `updater.py` recomputes `spread_vs_brent` from March 2026 OSP/Oman-Dubai vs current Brent (shows about -$40). Needs a rule: only compare same-month values, else show n/a.
2. History rows are keyed by the day the script ran, not the EIA observation date, so one stale Brent value repeats across many days. Key by observation period instead.
3. Stale manual values: Oman-Dubai, Urals, TTF, JKM (all 2026-03-21), OSP month (March 2026), chokepoint dates, "Crisis at a glance · July 2026" on the homepage. Brent/WTI now have live quotes (see data/live.json); the rest still need a source. EU gas storage and Hormuz transits are now automated (see data/gas-storage.json, data/chokepoints-live.json); the static July storage block and static chokepoint cards remain dated snapshots. For the rest, show the as-of date prominently.
4. News pipeline: `events.json` has no new timeline entries since 28 Jul 2026 and `_updated` is stale, though `_news_checked` advances daily. The script swallows API/fetch errors and still reports success. Check the Actions logs, then make it fail loudly (count errors, exit non-zero).
5. `README.md` documents a `core5.json` workflow that no longer exists. Rewrite or delete.
6. `news_update.py` user-agent still points at the old pacho064.github.io domain.
7. Content gaps: buyer-exposure (March 2026), OSP decoder (May-Oct missing), grades (API vs sulphur plot), no Iran page.

## Repo
github.com/pacho064/Contango, `gh` authenticated as pacho064. Local path `/Users/parthmulay/Contango`. Load nvm each session: `export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"`.
