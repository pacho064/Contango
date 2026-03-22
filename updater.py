"""
Contango Energy — daily price updater
Fetches Brent, WTI, Dubai from EIA. Runs on Render.com as a cron job.
Updates data/prices.json in the GitHub repo.
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Config (set these as environment variables in Render) ──────────────
EIA_KEY     = os.environ.get("EIA_API_KEY", "")
GH_TOKEN    = os.environ.get("GH_TOKEN", "")
GH_REPO     = os.environ.get("GH_REPO", "pacho064/Contango")
GH_FILE     = "data/prices.json"
GH_BRANCH   = "main"

# ── EIA series IDs ─────────────────────────────────────────────────────
EIA_SERIES = {
    "brent": "RBRTE",    # Europe Brent Spot Price FOB
    "wti":   "RWTC",     # WTI Cushing Spot Price
    "dubai": "EER_EPJK_PF4_RGN_DPB",  # Dubai/Fateh spot
    "hh":    "NG.RNGWHHD.D",          # Henry Hub natural gas daily
}

def fetch_eia_price(series_id):
    """Fetch latest daily price from EIA API. Returns (price, prev_price, date)."""
    url = (
        f"https://api.eia.gov/v2/petroleum/pri/spt/data/"
        f"?api_key={EIA_KEY}"
        f"&frequency=daily"
        f"&data[0]=value"
        f"&facets[series][]={series_id}"
        f"&sort[0][column]=period"
        f"&sort[0][direction]=desc"
        f"&length=2"
    )
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        rows = data.get("response", {}).get("data", [])
        if len(rows) >= 2:
            cur  = float(rows[0]["value"])
            prev = float(rows[1]["value"])
            date = rows[0]["period"]
            return round(cur, 2), round(prev, 2), date
        elif len(rows) == 1:
            cur  = float(rows[0]["value"])
            date = rows[0]["period"]
            return round(cur, 2), round(cur, 2), date
    except Exception as e:
        print(f"  EIA fetch failed for {series_id}: {e}")
    return None, None, None

def fetch_eia_gas(series_id):
    """Fetch latest Henry Hub gas price (different EIA endpoint)."""
    url = (
        f"https://api.eia.gov/v2/natural-gas/pri/fut/data/"
        f"?api_key={EIA_KEY}"
        f"&frequency=daily"
        f"&data[0]=value"
        f"&facets[series][]={series_id}"
        f"&sort[0][column]=period"
        f"&sort[0][direction]=desc"
        f"&length=2"
    )
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        rows = data.get("response", {}).get("data", [])
        if rows:
            return round(float(rows[0]["value"]), 3), rows[0]["period"]
    except Exception as e:
        print(f"  EIA gas fetch failed: {e}")
    return None, None

def get_current_prices_json():
    """Download the current prices.json from GitHub."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_FILE}?ref={GH_BRANCH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        response = json.loads(r.read())
    import base64
    content = base64.b64decode(response["content"]).decode("utf-8")
    return json.loads(content), response["sha"]

def push_prices_json(data, sha):
    """Push updated prices.json back to GitHub."""
    import base64
    content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
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
        "X-GitHub-Api-Version": "2022-11-28"
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        result = json.loads(r.read())
    print(f"  GitHub push: {result.get('commit', {}).get('sha', 'ok')[:8]}")

def main():
    print(f"\n{'='*50}")
    print(f"Contango price updater — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}")

    if not EIA_KEY:
        print("ERROR: EIA_API_KEY not set")
        return
    if not GH_TOKEN:
        print("ERROR: GH_TOKEN not set")
        return

    # ── Fetch prices from EIA ─────────────────────────────────────────
    print("\nFetching from EIA...")

    brent, brent_prev, brent_date = fetch_eia_price(EIA_SERIES["brent"])
    wti,   wti_prev,   wti_date   = fetch_eia_price(EIA_SERIES["wti"])
    dubai, dubai_prev, dubai_date = fetch_eia_price(EIA_SERIES["dubai"])
    hh, hh_date                   = fetch_eia_gas(EIA_SERIES["hh"])

    print(f"  Brent: ${brent} ({brent_date})")
    print(f"  WTI:   ${wti} ({wti_date})")
    print(f"  Dubai: ${dubai} ({dubai_date})")
    print(f"  HH gas: ${hh} ({hh_date})")

    # ── Load current prices.json ──────────────────────────────────────
    print("\nLoading current prices.json from GitHub...")
    try:
        prices, sha = get_current_prices_json()
    except Exception as e:
        print(f"ERROR loading prices.json: {e}")
        return

    # ── Update benchmarks ─────────────────────────────────────────────
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    today   = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def chg(cur, prev):
        if cur and prev and prev != 0:
            return round((cur - prev) / prev * 100, 2)
        return 0.0

    if brent:
        prices["benchmarks"]["brent"].update({
            "price": brent,
            "change_pct": chg(brent, brent_prev),
            "updated": brent_date or today,
            "source": "EIA spot (RBRTE)"
        })

    if wti:
        prices["benchmarks"]["wti"].update({
            "price": wti,
            "change_pct": chg(wti, wti_prev),
            "updated": wti_date or today,
            "source": "EIA spot (RWTC)"
        })

    if dubai:
        prices["benchmarks"]["dubai"] = {
            "price": dubai,
            "change_pct": chg(dubai, dubai_prev),
            "updated": dubai_date or today,
            "source": "EIA spot (Dubai/Fateh)"
        }

    if hh:
        prices["benchmarks"]["henry_hub"] = {
            "price": hh,
            "change_pct": 0.0,
            "updated": hh_date or today,
            "source": "EIA Henry Hub natural gas"
        }

    # ── Recalculate OSP spreads vs new Brent ─────────────────────────
    if brent and "osps" in prices:
        for key, osp in prices["osps"].items():
            osp["spread_vs_brent"] = round(osp["price"] - brent, 2)
        print(f"\n  OSP spreads recalculated vs Brent ${brent}")

    prices["_updated"] = now_iso

    # ── Push back to GitHub ───────────────────────────────────────────
    print("\nPushing updated prices.json to GitHub...")
    try:
        push_prices_json(prices, sha)
        print("  Done.")
    except Exception as e:
        print(f"ERROR pushing to GitHub: {e}")

if __name__ == "__main__":
    main()
```

Save and commit it with message `add price updater`.

---

**Step 2 — Create a file called `requirements.txt` in the root**

Create `requirements.txt` (in the root folder, same level as `index.html`). Paste this:
```
# No external libraries needed — only Python standard library
# This file tells Render.com it's a Python project