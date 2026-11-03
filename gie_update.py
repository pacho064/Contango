"""
Contango Energy — EU gas storage -> data/gas-storage.json

Source: GIE AGSI (Gas Infrastructure Europe), free, personal API key.
  https://agsi.gie.eu/api   (key goes in the x-key header)
Register for a key at https://agsi.gie.eu -> Account -> API.
Required secret / env var: GIE_API_KEY

Run locally:
    GIE_API_KEY=your_key python3 gie_update.py
    python3 -m http.server 8000      # then open http://localhost:8000

Editorial rules this script follows:
  - Publishes GIE's own EU-aggregate figures with GIE's own gas-day date.
  - The only arithmetic is: (a) the point difference between the latest fill
    and GIE's value for the same calendar day one year earlier, and (b) the same
    against the plain mean of GIE's values for the same calendar day in each of
    the previous five years. Each is left null if any needed day is missing.
    Labelled as computed on the page. No forecast, no target-hit estimate.
  - If the request fails, the key is missing, or no usable EU row comes back,
    the script exits non-zero (the GitHub Action turns red) and the previous
    file is left untouched.
  - Nothing changed since the last run -> the file is not rewritten.
"""

import os, sys, json, datetime, urllib.request, urllib.parse, urllib.error
from pathlib import Path

API_URL = os.environ.get("GIE_URL", "https://agsi.gie.eu/api")
OUT_PATH = Path("data/gas-storage.json")
HISTORY_YEARS = 5
PAGE_SIZE = 300
MAX_PAGES = 12            # hard stop so a pagination bug can never loop forever
SERIES_DAYS = 120


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def api_get(params, key):
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "x-key": key,
        "User-Agent": "ContangoEnergy/1.0 (+https://contango-energy.com)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        hint = {401: "key missing/invalid", 403: "key rejected", 429: "rate limit hit"}.get(e.code, "")
        fail(f"GIE request failed: HTTP {e.code} {hint}".strip())
    except Exception as e:
        fail(f"GIE request failed: {e}")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch_eu(key, since):
    rows, page = {}, 1
    while page <= MAX_PAGES:
        resp = api_get({"country": "eu", "from": since.isoformat(), "size": PAGE_SIZE, "page": page}, key)
        data = resp.get("data") if isinstance(resp, dict) else None
        if not isinstance(data, list):
            fail("GIE answered but the response had no data list.")
        for r in data:
            if not isinstance(r, dict):
                continue
            try:
                d = datetime.date.fromisoformat(str(r.get("gasDayStart"))[:10])
            except ValueError:
                continue
            full = num(r.get("full"))
            if full is None:
                continue
            rows[d] = r
        last = resp.get("last_page")
        if not isinstance(last, int) or page >= last:
            break
        page += 1
    if not rows:
        fail("No usable EU storage rows returned.")
    return rows


def pct_on(rows, d):
    r = rows.get(d)
    return num(r.get("full")) if r else None


def years_back(d, n):
    try:
        return d.replace(year=d.year - n)
    except ValueError:        # 29 Feb
        return d.replace(year=d.year - n, day=28)


def main():
    key = os.environ.get("GIE_API_KEY", "").strip()
    if not key:
        fail("GIE_API_KEY not set.")

    today = datetime.date.today()
    rows = fetch_eu(key, years_back(today, HISTORY_YEARS + 1) - datetime.timedelta(days=7))
    dates = sorted(rows)
    ld = dates[-1]
    r = rows[ld]
    full = num(r.get("full"))

    ya_day = years_back(ld, 1)
    ya = pct_on(rows, ya_day)
    past = [(years_back(ld, n), pct_on(rows, years_back(ld, n))) for n in range(1, HISTORY_YEARS + 1)]
    avg5 = None
    if all(v is not None for _, v in past):
        avg5 = round(sum(v for _, v in past) / HISTORY_YEARS, 2)

    body = {
        "source": {
            "name": "GIE AGSI",
            "url": "https://agsi.gie.eu/",
            "note": "EU aggregate of member-state storage operator data; revised by GIE after first publication.",
        },
        "eu": {
            "gas_day": ld.isoformat(),
            "full_pct": round(full, 2),
            "gas_in_storage_twh": num(r.get("gasInStorage")),
            "working_gas_volume_twh": num(r.get("workingGasVolume")),
            "injection_gwh": num(r.get("injection")),
            "withdrawal_gwh": num(r.get("withdrawal")),
            "status": r.get("status"),
            "year_earlier": {"gas_day": ya_day.isoformat(), "full_pct": ya},
            "vs_year_earlier_pts_computed": None if ya is None else round(full - ya, 2),
            "avg_prior_5y_full_pct_computed": avg5,
            "vs_avg_prior_5y_pts_computed": None if avg5 is None else round(full - avg5, 2),
            "series": [{"gas_day": d.isoformat(), "full_pct": num(rows[d].get("full"))} for d in dates[-SERIES_DAYS:]],
        },
    }

    existing = {}
    if OUT_PATH.exists():
        try:
            existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    if {k: v for k, v in existing.items() if not k.startswith("_")} == body:
        print("No change since last run - file left as is.")
        return

    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    out = {
        "_note": "Written by gie_update.py from GIE AGSI. gas_day is the source's own day, not the date this file was written.",
        "_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.update(body)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {OUT_PATH}: gas day {ld} full={full:.2f}% vs_year={body['eu']['vs_year_earlier_pts_computed']} vs_5y={body['eu']['vs_avg_prior_5y_pts_computed']}")


if __name__ == "__main__":
    main()
