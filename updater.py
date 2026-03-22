"""
Contango Energy — daily price updater
Runs hourly via GitHub Actions (.github/workflows/update.yml)

What it does:
  1. Fetches Brent + WTI from EIA API (free, official, reliable)
  2. Fetches Oman/Dubai, Urals, TTF, JKM from OilPriceAPI (free tier)
  3. Recomputes OSP absolute prices from stored monthly differentials + live Oman/Dubai
  4. Pushes updated data/prices.json back to GitHub

Environment variables required (set in GitHub Actions secrets):
  EIA_API_KEY      — from eia.gov/opendata (free, instant)
  OILPRICE_API_KEY — from oilpriceapi.com (free tier)
  GH_TOKEN         — GitHub personal access token with repo write scope
  GH_REPO          — e.g. pacho064/Contango (optional, defaults to this)
"""

import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Config ─────────────────────────────────────────────────────────────
EIA_KEY       = os.environ.get("EIA_API_KEY", "")
OILPRICE_KEY  = os.environ.get("OILPRICE_API_KEY", "")
GH_TOKEN      = os.environ.get("GH_TOKEN", "")
GH_REPO       = os.environ.get("GH_REPO", "pacho064/Contango")
GH_FILE       = "data/prices.json"
GH_BRANCH     = "main"

# ── EIA series IDs ─────────────────────────────────────────────────────
EIA_SERIES = {
    "brent": "RBRTE",   # Europe Brent Spot Price FOB $/bbl
    "wti":   "RWTC",    # WTI Cushing Spot Price $/bbl
}

# ── OilPriceAPI commodity codes ────────────────────────────────────────
OILPRICE_CODES = {
    "oman_dubai": "DME_OMAN_USD",
    "urals":      "URALS_CRUDE_USD",
    "ttf":        "DUTCH_TTF_EUR",
    "jkm":        "JKM_LNG_USD",
}


# ═══════════════════════════════════════════════════════════════════════
# EIA fetch
# ═══════════════════════════════════════════════════════════════════════

def fetch_eia(series_id):
    """Returns (price, prev_price, date_str) or (None, None, None) on failure."""
    url = (
        "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        f"?api_key={EIA_KEY}"
        "&frequency=daily"
        "&data[0]=value"
        f"&facets[series][]={series_id}"
        "&sort[0][column]=period"
        "&sort[0][direction]=desc"
        "&length=2"
    )
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        rows = data.get("response", {}).get("data", [])
        if len(rows) >= 2:
            return round(float(rows[0]["value"]), 2), round(float(rows[1]["value"]), 2), rows[0]["period"]
        elif len(rows) == 1:
            cur = round(float(rows[0]["value"]), 2)
            return cur, cur, rows[0]["period"]
    except Exception as e:
        print(f"  EIA fetch failed ({series_id}): {e}")
    return None, None, None


# ═══════════════════════════════════════════════════════════════════════
# OilPriceAPI fetch
# ═══════════════════════════════════════════════════════════════════════

def fetch_oilprice(codes_dict):
    """
    Fetch multiple codes in one request.
    Returns dict: { our_key: {"price": float, "updated": str} }
    """
    if not OILPRICE_KEY:
        print("  OILPRICE_API_KEY not set — skipping OilPriceAPI")
        return {}

    codes_str = ",".join(codes_dict.values())
    url = f"https://api.oilpriceapi.com/v1/prices/latest?by_code={codes_str}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Token {OILPRICE_KEY}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
    except Exception as e:
        print(f"  OilPriceAPI fetch failed: {e}")
        return {}

    raw = result.get("data", [])
    if isinstance(raw, dict):
        raw = [raw]

    # Invert codes_dict so we can look up by API code
    code_to_key = {v: k for k, v in codes_dict.items()}
    out = {}
    for item in raw:
        api_code = item.get("code") or item.get("type", "")
        price    = item.get("price") or item.get("value")
        ts       = item.get("created_at") or item.get("timestamp", "")
        if api_code in code_to_key and price:
            our_key = code_to_key[api_code]
            out[our_key] = {
                "price":   round(float(price), 2),
                "updated": ts[:10] if ts else datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            }
            print(f"  {our_key}: ${price}")
    return out


# ═══════════════════════════════════════════════════════════════════════
# GitHub helpers
# ═══════════════════════════════════════════════════════════════════════

def gh_get(filepath):
    """Download a file from GitHub. Returns (parsed_json, sha)."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{filepath}?ref={GH_BRANCH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())
    content = base64.b64decode(resp["content"]).decode("utf-8")
    return json.loads(content), resp["sha"]


def gh_put(filepath, data, sha, message):
    """Push a file to GitHub."""
    content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    payload = json.dumps({
        "message": message,
        "content": content,
        "sha":     sha,
        "branch":  GH_BRANCH,
    }).encode()
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{filepath}"
    req = urllib.request.Request(url, data=payload, method="PUT", headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        result = json.loads(r.read())
    return result.get("commit", {}).get("sha", "")[:8]


# ═══════════════════════════════════════════════════════════════════════
# OSP recalculation
# ═══════════════════════════════════════════════════════════════════════

def recalc_osps(data, oman_dubai_price, brent_price):
    """
    Recompute absolute OSP prices from stored differentials + live Oman/Dubai.
    Also recomputes spread_vs_brent.
    """
    if "osps" not in data:
        return
    updated = 0
    for key, osp in data["osps"].items():
        if key == "_note":
            continue
        diff = osp.get("differential_vs_omd")
        if diff is None:
            continue
        osp["price"]          = round(oman_dubai_price + diff, 2)
        osp["spread_vs_brent"] = round(osp["price"] - brent_price, 2)
        updated += 1
    print(f"  Recalculated {updated} OSP absolute prices vs Oman/Dubai ${oman_dubai_price}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    print(f"\n{'='*55}")
    print(f"Contango updater — {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}")

    if not GH_TOKEN:
        print("ERROR: GH_TOKEN not set"); return

    # ── 1. Fetch EIA benchmarks ─────────────────────────────────────────
    print("\n[1] EIA — Brent + WTI")
    eia_results = {}
    for key, series in EIA_SERIES.items():
        price, prev, date = fetch_eia(series)
        if price:
            chg = round((price - prev) / prev * 100, 2) if prev else 0.0
            eia_results[key] = {"price": price, "change_pct": chg, "updated": date or today}
            print(f"  {key}: ${price} ({chg:+.2f}%)")
        else:
            print(f"  {key}: fetch failed — keeping existing value")

    # ── 2. Fetch OilPriceAPI ────────────────────────────────────────────
    print("\n[2] OilPriceAPI — Oman/Dubai, Urals, TTF, JKM")
    op_results = fetch_oilprice(OILPRICE_CODES)

    # ── 3. Load current prices.json ─────────────────────────────────────
    print("\n[3] Loading prices.json from GitHub")
    try:
        data, sha = gh_get(GH_FILE)
    except Exception as e:
        print(f"  ERROR loading: {e}"); return

    # ── 4. Update benchmarks ────────────────────────────────────────────
    print("\n[4] Updating benchmarks")
    b = data.setdefault("benchmarks", {})

    for key, vals in eia_results.items():
        if key not in b:
            b[key] = {}
        b[key].update(vals)
        b[key]["source"] = f"EIA ({EIA_SERIES[key]})"

    op_source_labels = {
        "oman_dubai": "OilPriceAPI / DME",
        "urals":      "OilPriceAPI / Argus",
        "ttf":        "OilPriceAPI / ICE TTF",
        "jkm":        "OilPriceAPI / Platts JKM",
    }
    for key, vals in op_results.items():
        if key not in b:
            b[key] = {}
        b[key]["price"]   = vals["price"]
        b[key]["updated"] = vals["updated"]
        b[key]["source"]  = op_source_labels.get(key, "OilPriceAPI")

    # ── 5. Recalculate OSPs ─────────────────────────────────────────────
    print("\n[5] Recalculating OSP absolute prices")
    oman_dubai = b.get("oman_dubai", {}).get("price")
    brent      = b.get("brent",      {}).get("price")

    if oman_dubai and brent:
        recalc_osps(data, oman_dubai, brent)
    else:
        print(f"  Skipping OSP recalc — missing oman_dubai ({oman_dubai}) or brent ({brent})")

    # ── 6. Timestamp and push ───────────────────────────────────────────
    data["_updated"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    print("\n[6] Pushing to GitHub")
    try:
        commit = gh_put(
            GH_FILE, data, sha,
            f"prices: auto-update {now.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        print(f"  Done — commit {commit}")
    except Exception as e:
        print(f"  Push failed: {e}")

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
