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

def fetch_latest(series_id, api_key, label):
    """Fetch just the most recent (value, period) for a series. Used for
    monthly volume series (production, inventories) where only the latest
    observation matters. Returns (None, None) on failure."""
    vals = fetch(series_id, api_key)
    if vals:
        value, period = vals[0]
        print(f"  {label}: {value:,.1f}  [{period}]")
        return value, period
    return None, None

def write_history(existing, today):
    """Append (or update, if today already exists) one daily row to the
    crude price time-series in JSON Lines format. Pure local file work —
    does not touch prices.json or hit any API."""
    history_path = Path("data/history/crude-daily.jsonl")
    history_path.parent.mkdir(parents=True, exist_ok=True)

    benchmarks = existing.get("benchmarks", {}) or {}
    brent = benchmarks.get("brent") if isinstance(benchmarks.get("brent"), dict) else {}
    wti = benchmarks.get("wti") if isinstance(benchmarks.get("wti"), dict) else {}

    osps = existing.get("osps", {}) or {}
    arab = osps.get("arab_light") if isinstance(osps, dict) and isinstance(osps.get("arab_light"), dict) else {}

    production = existing.get("production", {}) or {}
    saudi = production.get("saudi_arabia") if isinstance(production.get("saudi_arabia"), dict) else {}
    iraq = production.get("iraq") if isinstance(production.get("iraq"), dict) else {}
    spr = existing.get("spr") if isinstance(existing.get("spr"), dict) else {}

    entry = {
        "date": today,
        "brent": brent.get("price"),
        "brent_change_pct": brent.get("change_pct"),
        "wti": wti.get("price"),
        "wti_change_pct": wti.get("change_pct"),
        "arab_light_osp": arab.get("price"),
        "arab_light_spread_vs_brent": arab.get("spread_vs_brent"),
        "saudi_crude_kbd": saudi.get("value"),
        "iraq_crude_kbd": iraq.get("value"),
        "us_spr_kbbl": spr.get("value"),
    }
    line = json.dumps(entry)

    # Idempotent: if today's date is already present, rewrite that line in
    # place; otherwise append a single line (no full-file rewrite).
    existing_lines = []
    if history_path.exists():
        existing_lines = history_path.read_text(encoding="utf-8").splitlines()

    replaced = False
    out = []
    for ln in existing_lines:
        if not ln.strip():
            continue
        try:
            rec = json.loads(ln)
        except Exception:
            out.append(ln)  # preserve anything unparseable rather than drop it
            continue
        if rec.get("date") == today:
            out.append(line)
            replaced = True
        else:
            out.append(ln)

    if replaced:
        history_path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"History: updated entry for {today} in {history_path}")
    else:
        with history_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(f"History: appended entry for {today} to {history_path}")


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

    # Monthly crude oil production (EIA International Energy Statistics:
    # product 57 = crude incl. lease condensate, activity 1 = production, TBPD)
    print("Fetching monthly production & inventories...")
    production = existing.setdefault("production", {})
    saudi_val, saudi_period = fetch_latest("INTL.57-1-SAU-TBPD.M", api_key, "saudi crude prod")
    if saudi_val is not None:
        production["saudi_arabia"] = {
            "value": round(saudi_val, 1), "unit": "thousand bbl/day", "period": saudi_period,
            "grade": "crude incl. lease condensate", "source": "EIA (INTL.57-1-SAU)"}
    iraq_val, iraq_period = fetch_latest("INTL.57-1-IRQ-TBPD.M", api_key, "iraq crude prod ")
    if iraq_val is not None:
        production["iraq"] = {
            "value": round(iraq_val, 1), "unit": "thousand bbl/day", "period": iraq_period,
            "grade": "crude incl. lease condensate", "source": "EIA (INTL.57-1-IRQ)"}

    # U.S. Strategic Petroleum Reserve crude stocks (monthly)
    spr_val, spr_period = fetch_latest("PET.MCSSTUS1.M", api_key, "us spr stocks ")
    if spr_val is not None:
        existing["spr"] = {
            "value": round(spr_val, 0), "unit": "thousand barrels", "period": spr_period,
            "description": "U.S. crude oil in Strategic Petroleum Reserve", "source": "EIA (MCSSTUS1)"}

    existing["_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
    prices_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    print(f"Done. Saved to {prices_path}")

    # Also append today's row to the long-lived time-series history.
    write_history(existing, today)

if __name__ == "__main__":
    main()
