"""
Contango Energy — chokepoint daily transits -> data/chokepoints-live.json

Source: IMF PortWatch (Oxford / UN Global Pulse AIS-derived), free, no key.
  Daily_Chokepoints_Data feature service.  https://portwatch.imf.org
Chokepoints: Strait of Hormuz, Bab el-Mandeb, Suez Canal, Cape of Good Hope
(the Cape shows ships rerouting around Africa).

Run locally:
    python3 portwatch_update.py
    python3 -m http.server 8000      # then open http://localhost:8000

Editorial rules this script follows:
  - Publishes PortWatch's own daily counts with their own dates. PortWatch runs
    several days behind real time; the page always shows the data date.
  - Chokepoints are found by NAME in PortWatch's own table, and each must resolve
    to exactly one portid whose name matches. A chokepoint that cannot be
    resolved is left out and recorded under "unresolved"; its old data is never
    shown as current.
  - The only arithmetic is a plain 7-day mean of PortWatch's daily totals, the
    same 7 dates one year earlier, and the percentage change between those two
    means. All are labelled "computed" and are null if any day is missing. No
    baseline is chosen or assumed by us.
  - Hormuz failing, or nothing resolving, exits non-zero (the GitHub Action turns
    red) and the previous file is left untouched.
  - Nothing changed since the last run -> the file is not rewritten.
"""

import os, sys, json, datetime, urllib.request, urllib.parse, urllib.error
from pathlib import Path

SERVICE_URL = os.environ.get(
    "PORTWATCH_URL",
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query",
)
# key, label shown on the page, UPPERCASE text that must appear in PortWatch's portname,
# expected portid if we have confirmed one (Hormuz = chokepoint6 per PortWatch)
CHOKEPOINTS = [
    ("hormuz",        "Strait of Hormuz",  "HORMUZ",          "chokepoint6"),
    ("bab_el_mandeb", "Bab el-Mandeb",     "MANDEB",          None),
    ("suez",          "Suez Canal",        "SUEZ",            None),
    ("cape",          "Cape of Good Hope", "CAPE OF GOOD",    None),
]
CORE_KEY = "hormuz"
ROWS = 400            # ~13 months: enough for last-year comparison
SERIES_DAYS = 60      # how many daily rows the page gets
OUT_PATH = Path("data/chokepoints-live.json")

FIELDS = ["date", "portid", "portname", "n_total", "n_tanker", "n_cargo",
          "n_container", "n_dry_bulk", "n_general_cargo", "n_roro", "capacity"]


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print("WARNING: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg.replace("\n", " "))


class QueryError(Exception):
    pass


def query(params):
    url = SERVICE_URL + "?" + urllib.parse.urlencode(dict(params, f="json"))
    req = urllib.request.Request(url, headers={
        "User-Agent": "ContangoEnergy/1.0 (+https://contango-energy.com)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read())
    except Exception as e:
        raise QueryError(f"PortWatch request failed: {e}")
    if isinstance(body, dict) and body.get("error"):
        raise QueryError(f"PortWatch returned an error: {str(body['error'])[:200]}")
    feats = body.get("features") if isinstance(body, dict) else None
    if not isinstance(feats, list):
        raise QueryError("PortWatch answered but the response had no feature list.")
    return [f.get("attributes") for f in feats if isinstance(f, dict) and isinstance(f.get("attributes"), dict)]


def resolve_ports():
    """Map our keys to PortWatch portids by name. Returns (resolved, unresolved)."""
    like = " OR ".join(f"UPPER(portname) LIKE '%{pat}%'" for _, _, pat, _ in CHOKEPOINTS)
    rows = query({"where": like, "outFields": "portid,portname", "returnDistinctValues": "true",
                  "returnGeometry": "false", "resultRecordCount": "200"})
    resolved, unresolved = {}, {}
    for key, label, pat, expect in CHOKEPOINTS:
        hits = {(r.get("portid"), str(r.get("portname") or "")) for r in rows
                if pat in str(r.get("portname") or "").upper() and r.get("portid")}
        ids = {pid for pid, _ in hits}
        if len(ids) != 1:
            unresolved[key] = f"expected exactly one PortWatch series matching '{pat}', found {len(ids)}: {sorted(ids)[:4]}"
        elif expect and next(iter(ids)) != expect:
            unresolved[key] = f"'{pat}' resolved to {next(iter(ids))}, not the confirmed {expect} - refusing to publish"
        else:
            pid = next(iter(ids))
            resolved[key] = (pid, sorted(n for p, n in hits if p == pid)[0])
    return resolved, unresolved


def fetch_series(portid):
    rows = query({"where": f"portid='{portid}'", "outFields": ",".join(FIELDS),
                  "orderByFields": "date DESC", "resultRecordCount": str(ROWS)})
    if not rows:
        raise QueryError("no rows returned")
    return rows


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


def clean(rows, portid):
    by_date = {}
    for a in rows:
        if a.get("portid") != portid:
            continue
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
        raise QueryError("no usable rows after cleaning")
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


def build_one(portid, name, label):
    by_date = clean(fetch_series(portid), portid)
    dates = sorted(by_date)
    latest_d = dates[-1]
    a, y = mean7(by_date, latest_d), mean7(by_date, year_earlier(latest_d))
    pct = None
    if a and y and y["value"] > 0:
        pct = round((a["value"] - y["value"]) / y["value"] * 100, 1)
    return {
        "label": label,
        "portid": portid,
        "portname": name,
        "latest": by_date[latest_d],
        "avg7_computed": a,
        "avg7_year_earlier_computed": y,
        "change_vs_year_earlier_pct_computed": pct,
        "series": [by_date[d] for d in dates[-SERIES_DAYS:]],
    }


def main():
    try:
        resolved, unresolved = resolve_ports()
    except QueryError as e:
        fail(str(e))

    chokepoints = {}
    for key, label, _, _ in CHOKEPOINTS:
        if key not in resolved:
            continue
        pid, name = resolved[key]
        try:
            chokepoints[key] = build_one(pid, name, label)
        except QueryError as e:
            unresolved[key] = f"{pid}: {e}"

    for key, why in unresolved.items():
        warn(f"{key}: {why}")
    if CORE_KEY not in chokepoints:
        fail("Strait of Hormuz could not be published - refusing to write the file. " + unresolved.get(CORE_KEY, ""))

    body = {
        "source": {
            "name": "IMF PortWatch",
            "url": "https://portwatch.imf.org/",
            "note": "AIS-derived daily vessel transit counts; published with a lag of several days.",
        },
        "chokepoints": chokepoints,
        "unresolved": unresolved,
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
    for key, c in chokepoints.items():
        l = c["latest"]
        print(f"Saved {key}: {l['date']} total={l['n_total']} avg7={(c['avg7_computed'] or {}).get('value')} "
              f"vs year earlier {c['change_vs_year_earlier_pct_computed']}%")
    if unresolved:
        print(f"Left out: {', '.join(unresolved)}")


if __name__ == "__main__":
    main()
