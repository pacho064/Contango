"""
Contango Energy — price updater
Fetches prices from OilPriceAPI (free tier).
Runs on Render.com as a cron job.
Updates data/prices.json in GitHub repo.
"""

import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Config from Render environment variables ───────────────────────────
OILPRICE_KEY = os.environ.get("OILPRICE_API_KEY", "")
GH_TOKEN     = os.environ.get("GH_TOKEN", "")
GH_REPO      = os.environ.get("GH_REPO", "pacho064/Contango")
GH_FILE      = "data/prices.json"
GH_BRANCH    = "main"

# ── Commodity codes from OilPriceAPI ──────────────────────────────────
# All available on free tier
CODES = [
    # Global benchmarks
    "BRENT_CRUDE_USD",
    "WTI_USD",
    "DUBAI_CRUDE_USD",
    "DME_OMAN_USD",
    "MURBAN_CRUDE_USD",
    "URALS_CRUDE_USD",
    "OPEC_BASKET_USD",
    # Refined products
    "GASOLINE_RBOB_USD",
    "ULSD_DIESEL_USD",
    "JET_FUEL_USD",
    "HEATING_OIL_USD",
    # Natural gas
    "DUTCH_TTF_EUR",
    "JKM_LNG_USD",
    "NATURAL_GAS_USD",
]

def fetch_prices(codes):
    """Fetch latest prices for multiple commodity codes in one request."""
    codes_str = ",".join(codes)
    url = f"https://api.oilpriceapi.com/v1/prices/latest?by_code={codes_str}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Token {OILPRICE_KEY}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  OilPriceAPI fetch failed: {e}")
        return None

def get_prices_json():
    """Download current prices.json from GitHub."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_FILE}?ref={GH_BRANCH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())
    content = base64.b64decode(resp["content"]).decode("utf-8")
    return json.loads(content), resp["sha"]

def push_prices_json(data, sha):
    """Push updated prices.json to GitHub."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    payload = json.dumps({
        "message": f"prices: auto-update {now}",
        "content": content,
        "sha": sha,
        "branch": GH_BRANCH
    }).encode()
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_FILE}"
    req = urllib.request.Request(url, data=payload, method="PUT", headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        result = json.loads(r.read())
    return result.get("commit", {}).get("sha", "")[:8]

def main():
    now = datetime.now(timezone.utc)
    print(f"\n{'='*55}")
    print(f"Contango updater — {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}")

    if not OILPRICE_KEY:
        print("ERROR: OILPRICE_API_KEY not set"); return
    if not GH_TOKEN:
        print("ERROR: GH_TOKEN not set"); return

    # ── Fetch all prices in one API call ────────────────────────────────
    print(f"\nFetching {len(CODES)} prices from OilPriceAPI...")
    result = fetch_prices(CODES)
    if not result:
        print("Fetch failed — aborting"); return

    # OilPriceAPI returns either a single object or array depending on query
    raw = result.get("data", [])
    if isinstance(raw, dict):
        raw = [raw]

    prices_by_code = {}
    for item in raw:
        code = item.get("code") or item.get("type", "")
        price = item.get("price") or item.get("value")
        ts = item.get("created_at") or item.get("timestamp", "")
        if code and price:
            prices_by_code[code] = {
                "price": round(float(price), 2),
                "updated": ts[:10] if ts else now.strftime("%Y-%m-%d"),
            }
            print(f"  {code}: ${price}")

    if not prices_by_code:
        print("No prices returned — aborting"); return

    # ── Load current prices.json ─────────────────────────────────────────
    print("\nLoading prices.json from GitHub...")
    try:
        data, sha = get_prices_json()
    except Exception as e:
        print(f"ERROR: {e}"); return

    today = now.strftime("%Y-%m-%d")

    # ── Map API codes to our data structure ─────────────────────────────
    def upd(section, key, code, source_label):
        if code in prices_by_code:
            p = prices_by_code[code]
            if key not in section:
                section[key] = {}
            section[key]["price"]   = p["price"]
            section[key]["updated"] = p["updated"]
            section[key]["source"]  = source_label

    b = data.setdefault("benchmarks", {})
    upd(b, "brent",       "BRENT_CRUDE_USD",  "OilPriceAPI / ICE")
    upd(b, "wti",         "WTI_USD",          "OilPriceAPI / CME")
    upd(b, "dubai",       "DUBAI_CRUDE_USD",  "OilPriceAPI / Platts")
    upd(b, "oman_dme",    "DME_OMAN_USD",     "OilPriceAPI / DME")
    upd(b, "murban",      "MURBAN_CRUDE_USD", "OilPriceAPI / ICE Murban")
    upd(b, "urals",       "URALS_CRUDE_USD",  "OilPriceAPI / Argus")
    upd(b, "opec_basket", "OPEC_BASKET_USD",  "OilPriceAPI / OPEC")

    r = data.setdefault("refined", {})
    upd(r, "rbob_gasoline", "GASOLINE_RBOB_USD", "OilPriceAPI / CME NYMEX")
    upd(r, "diesel_ulsd",   "ULSD_DIESEL_USD",   "OilPriceAPI / CME NYMEX")
    upd(r, "jet_fuel",      "JET_FUEL_USD",      "OilPriceAPI / IATA")
    upd(r, "heating_oil",   "HEATING_OIL_USD",   "OilPriceAPI / CME NYMEX")

    g = data.setdefault("gas", {})
    upd(g, "ttf",       "DUTCH_TTF_EUR",   "OilPriceAPI / ICE")
    upd(g, "jkm_lng",   "JKM_LNG_USD",    "OilPriceAPI / Platts")
    upd(g, "henry_hub", "NATURAL_GAS_USD", "OilPriceAPI / CME")

    # ── Recalculate OSP spreads vs Brent ────────────────────────────────
    brent_price = b.get("brent", {}).get("price")
    if brent_price and "osps" in data:
        for osp in data["osps"].values():
            if "price" in osp:
                osp["spread_vs_brent"] = round(osp["price"] - brent_price, 2)
        print(f"\n  OSP spreads recalculated vs Brent ${brent_price}")

    data["_updated"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Push to GitHub ───────────────────────────────────────────────────
    print("\nPushing to GitHub...")
    try:
        commit = push_prices_json(data, sha)
        print(f"  Done — commit {commit}")
    except Exception as e:
        print(f"  Push failed: {e}")

if __name__ == "__main__":
    main()