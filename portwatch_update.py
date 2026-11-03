"""
Contango Energy — Strait of Hormuz daily transits -> data/chokepoints-live.json

Source: IMF PortWatch (Oxford / UN Global Pulse AIS-derived), free, no key.
  Daily_Chokepoints_Data feature service, portid = chokepoint6 (Strait of Hormuz).
  https://portwatch.imf.org/pages/chokepoint6

Run locally:
    python3 portwatch_update.py
    python3 -m http.server 8000      # then open http://localhost:8000

Editorial rules this script follows:
  - Publishes PortWatch's own daily counts with their own dates. PortWatch runs
    several days behind real time; the page always shows the data date.
  - The only arithmetic is a plain 7-day mean of PortWatch's own daily totals,
    and the same 7-day mean for the same dates one year earlier. Both are
    labelled as computed, and are left out (null) if any day is missing.
    No baseline is chosen or assumed by us.
  - If the request fails, no rows come back, or the series is not the Strait of
    Hormuz, the script exits non-zero (the GitHub Action turns red) and the
    previous file is left untouched.
  - Nothing changed since the last run -> the file is not rewritten.
"""

import os, sys, json, datetime, urllib.request, urllib.parse, urllib.error
from pathlib import Path

SERVICE_URL = os.environ.get(
    "PORTWATCH_URL",
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query",
)
PORT_ID = "chokepoint6"
ROWS = 400            # ~13 months: enough for last-year comparison
SERIES_DAYS = 60      # how many daily rows the page gets
OUT_PATH = Path("data/chokepoints-live.json")

FIELDS = ["date", "portid", "portname", "n_total", "n_tanker", "n_cargo",
          "n_container", "n_dry_bulk", "n_general_cargo", "n_roro", "capacity"]


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def fetch_rows():
    params = {
        "where": f"portid='{PORT_ID}'",
        "outFields": ",".join(FIELDS),
        "orderByFields": "date DESC",
        "resultRecordCount": str(ROWS),
        "f": "json",
    }
    url = SERVICE_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "ContangoEnergy/1.0 (+https://contango-energy.com)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read())
    except Exception as e:
        fail(f"PortWatch request failed: {e}")
    if isinstance(body, dict) and body.get("error"):
        fail(f"PortWatch returned an error: {str(body['error'])[:200]}")
    feats = body.get("features") if isinstance(body, dict) else None
    if not isinstance(feats, list) or not feats:
        fail("PortWatch answered but returned no rows.")
    return [f.get("attributes") for f in feats if isinstance(f, dict) and isinstance(f.get("attributes"), dict)]


def parse_date(v):
    """ArcGIS dates are usually epoch milliseconds, sometimes ISO strings."""
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().isdigit()):
            return datetime.datetime.fromtimestamp(float(v) / 1000, datetime.timezone.utc).date()
        return datetime.date.fromisoformat(str(v).strip()[:10])
    except Exception:
        return None


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f == int(f) else round(f, 1)


def clean(rows):
    by_date = {}
    for a in rows:
        if a.get("portid") != PORT_ID:
            continue
        name = str(a.get("portname") or "")
        if "hormuz" not in name.lower():
            fail(f"portid {PORT_ID} is now named '{name}', not the Strait of Hormuz - refusing to publish.")
        d = parse_date(a.get("date"))
        total = num(a.get("n_total"))
        if d is None or total is None:
            continue
        by_date[d] = {
            "date": d.isoformat(),
            "n_total": total,
            "n_tanker": num(a.get("n_tanker")),
            "n_cargo": num(a.get("n_cargo")),
            "n_container": num(a.get("n_container")),
            "n_dry_bulk": num(a.get("n_dry_bulk")),
            "n_general_cargo": num(a.get("n_general_cargo")),
            "n_roro": num(a.get("n_roro")),
            "capacity_t": num(a.get("capacity")),
        }
    if not by_date:
        fail("No usable Hormuz rows after cleaning.")
    return by_date


def mean7(by_date, end):
    """Plain mean of n_total for the 7 days ending at `end`; None if any day is missing."""
    days = [end - datetime.timedelta(days=i) for i in range(7)]
    if any(d not in by_date for d in days):
        return None
    return {
        "value": round(sum(by_date[d]["n_total"] for d in days) / 7, 2),
        "from": min(days).isoformat(),
        "to": end.isoformat(),
    }


def year_earlier(d):
    try:
        return d.replace(year=d.year - 1)
    except ValueError:        # 29 Feb
        return d.replace(year=d.year - 1, day=28)


def main():
    by_date = clean(fetch_rows())
    dates = sorted(by_date)
    latest_d = dates[-1]

    series = [by_date[d] for d in dates[-SERIES_DAYS:]]
    body = {
        "source": {
            "name": "IMF PortWatch",
            "url": "https://portwatch.imf.org/pages/chokepoint6",
            "note": "AIS-derived daily vessel transit counts; published with a lag of several days.",
        },
        "hormuz": {
            "portid": PORT_ID,
            "latest": by_date[latest_d],
            "avg7_computed": mean7(by_date, latest_d),
            "avg7_year_earlier_computed": mean7(by_date, year_earlier(latest_d)),
            "series": series,
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
        "_note": "Written by portwatch_update.py from IMF PortWatch. Dates are UTC days of the source data, not the date this file was written.",
        "_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.update(body)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    l = by_date[latest_d]
    print(f"Saved {OUT_PATH}: {l['date']} total={l['n_total']} tanker={l['n_tanker']} "
          f"avg7={(body['hormuz']['avg7_computed'] or {}).get('value')}")


if __name__ == "__main__":
    main()
