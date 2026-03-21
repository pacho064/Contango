# Contango data files

This folder lets you update core numbers without editing `index.html`.

## File used now

- `core5.json`: controls the Core 5 board and event baseline panel.
- `core5_template.csv`: editable import template for quick updates.

## How to update values

1. Open `data/core5.json`.
2. Edit `currentValue` for each series.
3. If needed, edit `refValue` for Brent (used by spread calculation).
4. Save and refresh the site.

Or use one command (Python, recommended):

`python3 scripts/update_core5.py --brent 84.2 --arabl 86.1 --murban 87.3 --omd 85.6 --basram 83.9 --kec 84.4`

This command updates all 5 series and recalculates the lead spread input values.

Node version (if you install Node later):

`npm run core5:update -- --brent 84.2 --arabl 86.1 --murban 87.3 --omd 85.6 --basram 83.9 --kec 84.4`

## CSV import flow (easiest for research notes)

1. Edit `data/core5_template.csv`.
2. Run:

`python3 scripts/import_core5_csv.py --csv data/core5_template.csv`

Optional:

`python3 scripts/import_core5_csv.py --csv data/core5_template.csv --event-date 2026-02-01 --event-name "US-Iran war volatility baseline"`

CSV columns:
- `series_key`: must be one of `lead,murban,omd,basra,kec`
- `current_value`: latest value
- `ref_value`: required for `lead` row (Brent reference)
- `feb1_value`: event baseline value
- `source`: source label shown on UI
- `source_url`: optional primary-source link shown as clickable `source`

## Notes

- The page still has safe fallback values in `index.html`.
- If `core5.json` is missing or invalid, the site will keep working with fallback values.
- Use ISO date format (`YYYY-MM-DD`) for the event baseline date.
- Optional event update flags in the script:
  - `--event-date 2026-02-01`
  - `--event-name "US-Iran war volatility baseline"`
