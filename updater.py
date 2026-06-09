"""
Contango Energy — daily price updater
Runs via GitHub Actions at 18:00 UTC every weekday.

Fetches from EIA Open Data API (free):
  - Brent spot (RBRTE)
  - WTI spot (RWTC)
  - Oman/Dubai spot (falls back gracefully if unavailable)

Recalculates OSP absolute prices and spreads vs Brent.
"""

import os, json, sys, datetime, urllib.request, urllib.error
from pathlib import Path

EIA_BASE = "https://api.eia.gov/v2/seriesid/{}?api_key={}&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5"

SERIES = {
    "brent":      "PET.RBRTE.D",
    "wti":        "PET.RWTC.D",
    "oman_dubai": "PET.EER_EPJK_PF4_RGN_DPB.D",
}

def fetch_series(series_id, api_key):
    url = EIA_BASE.format(series_id, api_key)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("response", {}).get("data", [])
    except Exception as e:
        print(f"  WARNING: fetch failed for {series_id}: {e}", file=sys.stderr)
        return []

def latest_two(rows):
    vals = []
    for row in rows[:5]:
        try:
            v = float(row["value"])
            vals.append((v, row.get("period", "")))
        except (KeyError, TypeError, ValueError):
            continue
    if len(vals) >= 2:
        return vals[0], vals[1]
    elif len(vals) == 1:
        return vals[0], (None, "")
    return (None, ""), (None, "")

def change_pct(current, previous):
    if previous is None or previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 2)

def main():
    api_key = os.environ.get("EIA_API_KEY", "").strip()
    if not api_key:
        print("ERROR: EIA_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    prices_path = Path("data/prices.json")
    if not prices_path.exists():
        print(f"ERROR: {prices_path} not found.", file=sys.stderr)
        sys.exit(1)

    existing = json.loads(prices_path.read_text(encoding="utf-8"))
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    print(f"Contango price updater — {today}")
    print("Fetching EIA series...")

    # --- Fetch benchmarks ---
    fetched = {}
    for key, series_id in SERIES.items():
        rows = fetch_series(series_id, api_key)
        (cur, period), (prev, _) = latest_two(rows)
        if cur is not None:
            fetched[key] = {
                "price": round(cur, 2),
                "change_pct": change_pct(cur, prev),
                "updated": period or today,
            }
            print(f"  {key:15} ${cur:.2f}  ({fetched[key]['change_pct']:+.2f}%)  [{period}]")
        else:
            print(f"  {key:15} FAILED — keeping existing value")

    # --- Update benchmarks ---
    benchmarks = existing.setdefault("benchmarks", {})

    if "brent" in fetched:
        benchmarks["brent"] = {
            **({} if not isinstance(benchmarks.get("brent"), dict) else benchmarks["brent"]),
            "price": fetched["brent"]["price"],
            "change_pct": fetched["brent"]["change_pct"],
            "updated": fetched["brent"]["updated"],
            "source": "EIA (RBRTE)",
        }

    if "wti" in fetched:
        benchmarks["wti"] = {
            **({} if not isinstance(benchmarks.get("wti"), dict) else benchmarks["wti"]),
            "price": fetched["wti"]["price"],
            "change_pct": fetched["wti"]["change_pct"],
            "updated": fetched["wti"]["updated"],
            "source": "EIA (RWTC)",
        }

    if "oman_dubai" in fetched:
        omd_price = fetched["oman_dubai"]["price"]
        brent_price = benchmarks.get("brent", {}).get("price", 80) if isinstance(benchmarks.get("brent"), dict) else 80
        if abs(omd_price - brent_price) < 30 and omd_price > 10:
            benchmarks["oman_dubai"] = {
                **({} if not isinstance(benchmarks.get("oman_dubai"), dict) else benchmarks["oman_dubai"]),
                "price": omd_price,
                "change_pct": fetched["oman_dubai"]["change_pct"],
                "updated": fetched["oman_dubai"]["updated"],
                "source": "EIA (DME Oman)",
            }
            print(f"  Oman/Dubai updated: ${omd_price:.2f}")
        else:
            print(f"  Oman/Dubai SKIPPED (${omd_price:.2f} vs Brent ${brent_price:.2f} — sanity check failed)")

    # --- Recalculate OSP absolutes and spreads ---
    brent_price = benchmarks.get("brent", {}).get("price") if isinstance(benchmarks.get("brent"), dict) else None
    omd_price = benchmarks.get("oman_dubai", {}).get("price") if isinstance(benchmarks.get("oman_dubai"), dict) else None

    osps = existing.get("osps", {})
    if brent_price and osps:
        print("\nRecalculating OSP absolutes and spreads vs Brent...")
        for grade, osp in osps.items():
            # Fix: handle case where osp is a string instead of dict
            if not isinstance(osp, dict):
                print(f"  {grade:20} SKIPPED (malformed entry: {type(osp).__name__})")
                continue
            diff = osp.get("differential_vs_omd")
            if diff is not None and omd_price:
                new_abs = round(omd_price + diff, 2)
                new_spread = round(new_abs - brent_price, 2)
                osp["price"] = new_abs
                osp["spread_vs_brent"] = new_spread
                print(f"  {grade:20} ${new_abs:.2f}  (spread vs Brent: {new_spread:+.2f})")
            elif diff is not None and brent_price:
                # No Oman/Dubai — estimate from Brent with typical differential
                print(f"  {grade:20} SKIPPED (no Oman/Dubai price available)")

    # --- Stamp update time ---
    existing["_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
    existing["_updater"] = "updater.py"
    existing["_last_brent"] = brent_price

    # --- Write ---
    prices_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved to {prices_path}")

if __name__ == "__main__":
    main()
