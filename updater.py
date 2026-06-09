import os, json, sys, datetime, urllib.request
from pathlib import Path

EIA_BASE = "https://api.eia.gov/v2/seriesid/{}?api_key={}&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5"

def fetch(series_id, api_key):
    url = EIA_BASE.format(series_id, api_key)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        rows = data.get("response", {}).get("data", [])
        vals = []
        for row in rows[:5]:
            try:
                vals.append((float(row["value"]), row.get("period", "")))
            except:
                continue
        return vals
    except Exception as e:
        print(f"  WARNING: fetch failed for {series_id}: {e}", file=sys.stderr)
        return []

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

    benchmarks = existing.setdefault("benchmarks", {})

    # Brent
    brent_vals = fetch("PET.RBRTE.D", api_key)
    if brent_vals:
        cur, period = brent_vals[0]
        prev = brent_vals[1][0] if len(brent_vals) > 1 else cur
        chg = round((cur - prev) / prev * 100, 2) if prev else 0.0
        benchmarks["brent"] = {"price": round(cur,2), "change_pct": chg, "updated": period, "source": "EIA (RBRTE)"}
        print(f"  brent  ${cur:.2f}  ({chg:+.2f}%)  [{period}]")

    # WTI
    wti_vals = fetch("PET.RWTC.D", api_key)
    if wti_vals:
        cur, period = wti_vals[0]
        prev = wti_vals[1][0] if len(wti_vals) > 1 else cur
        chg = round((cur - prev) / prev * 100, 2) if prev else 0.0
        benchmarks["wti"] = {"price": round(cur,2), "change_pct": chg, "updated": period, "source": "EIA (RWTC)"}
        print(f"  wti    ${cur:.2f}  ({chg:+.2f}%)  [{period}]")

    # Recalculate OSP spreads vs Brent (safely)
    brent_price = benchmarks.get("brent", {}).get("price") if isinstance(benchmarks.get("brent"), dict) else None
    omd_price = benchmarks.get("oman_dubai", {}).get("price") if isinstance(benchmarks.get("oman_dubai"), dict) else None

    osps = existing.get("osps", {})
    if isinstance(osps, dict) and brent_price:
        print("Recalculating OSP spreads...")
        for grade, osp in list(osps.items()):
            if not isinstance(osp, dict):
                print(f"  {grade}: skipped (not a dict)")
                continue
            if grade.startswith("_"):
                continue
            diff = osp.get("differential_vs_omd")
            if diff is not None and omd_price:
                osp["price"] = round(omd_price + diff, 2)
                osp["spread_vs_brent"] = round(osp["price"] - brent_price, 2)
                print(f"  {grade}: ${osp['price']:.2f}")

    existing["_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
    prices_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    print(f"Done. Saved to {prices_path}")

if __name__ == "__main__":
    main()
