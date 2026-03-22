"""
Contango Energy — daily price updater
Runs daily at 18:00 UTC via GitHub Actions.
Uses EIA API only (free, official, no rate limits).

Fetches: Brent, WTI, Dubai/Fateh spot
Recalculates: all OSP absolute prices from stored differentials + live Dubai
Pushes: updated data/prices.json to GitHub

Secrets needed in GitHub Actions:
  EIA_API_KEY  — from eia.gov/opendata (free, instant)
  GH_TOKEN     — GitHub personal access token (repo write scope)
  GH_REPO      — auto-set by GitHub Actions via github.repository
"""

import os, json, base64, urllib.request
from datetime import datetime, timezone

EIA_KEY   = os.environ.get("EIA_API_KEY", "")
GH_TOKEN  = os.environ.get("GH_TOKEN", "")
GH_REPO   = os.environ.get("GH_REPO", "pacho064/Contango")
GH_FILE   = "data/prices.json"
GH_BRANCH = "main"

# EIA series — all petroleum spot prices endpoint
EIA_SERIES = {
    "brent":       "RBRTE",              # Europe Brent Spot FOB $/bbl
    "wti":         "RWTC",               # WTI Cushing Spot $/bbl
    "dubai":       "EER_EPJK_PF4_RGN_DPB",  # Dubai/Fateh Spot $/bbl
}

def fetch_eia(series_id):
    url = (
        "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        f"?api_key={EIA_KEY}"
        "&frequency=daily&data[0]=value"
        f"&facets[series][]={series_id}"
        "&sort[0][column]=period&sort[0][direction]=desc&length=2"
    )
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            rows = json.loads(r.read()).get("response", {}).get("data", [])
        if len(rows) >= 2:
            cur, prev = float(rows[0]["value"]), float(rows[1]["value"])
            return round(cur, 2), round((cur-prev)/prev*100, 2), rows[0]["period"]
        elif len(rows) == 1:
            cur = float(rows[0]["value"])
            return round(cur, 2), 0.0, rows[0]["period"]
    except Exception as e:
        print(f"  EIA fetch failed ({series_id}): {e}")
    return None, None, None

def gh_get(filepath):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{filepath}?ref={GH_BRANCH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())
    return json.loads(base64.b64decode(resp["content"]).decode()), resp["sha"]

def gh_put(filepath, data, sha, message):
    payload = json.dumps({
        "message": message,
        "content": base64.b64encode(json.dumps(data, indent=2).encode()).decode(),
        "sha": sha, "branch": GH_BRANCH,
    }).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GH_REPO}/contents/{filepath}",
        data=payload, method="PUT",
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read()).get("commit", {}).get("sha", "")[:8]

def recalc_osps(data, dubai_price, brent_price):
    """Recompute OSP absolutes from stored monthly differentials + live Dubai."""
    for key, osp in data.get("osps", {}).items():
        if key == "_note": continue
        diff = osp.get("differential_vs_omd")
        if diff is None: continue
        osp["price"]           = round(dubai_price + diff, 2)
        osp["spread_vs_brent"] = round(osp["price"] - brent_price, 2)

def main():
    now   = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    print(f"\n{'='*50}\nContango updater — {now.strftime('%Y-%m-%d %H:%M UTC')}\n{'='*50}")

    if not EIA_KEY:  print("ERROR: EIA_API_KEY not set"); return
    if not GH_TOKEN: print("ERROR: GH_TOKEN not set");    return

    # 1. Fetch from EIA
    print("\n[1] Fetching from EIA...")
    fetched = {}
    for key, series in EIA_SERIES.items():
        price, chg, date = fetch_eia(series)
        if price:
            fetched[key] = {"price": price, "change_pct": chg, "updated": date or today,
                            "source": f"EIA ({series})"}
            print(f"  {key}: ${price} ({chg:+.2f}%)")
        else:
            print(f"  {key}: failed — keeping existing")

    # 2. Load prices.json
    print("\n[2] Loading prices.json from GitHub...")
    try:
        data, sha = gh_get(GH_FILE)
    except Exception as e:
        print(f"  ERROR: {e}"); return

    # 3. Update benchmarks
    b = data.setdefault("benchmarks", {})
    for key, vals in fetched.items():
        b.setdefault(key, {}).update(vals)
    # Keep oman_dubai in sync with dubai spot (same price, different label)
    if "dubai" in fetched:
        b.setdefault("oman_dubai", {}).update({
            **fetched["dubai"],
            "source": "EIA Dubai/Fateh spot (proxy for Oman/Dubai)",
        })

    # 4. Recalculate OSPs
    dubai_price = b.get("dubai", {}).get("price") or b.get("oman_dubai", {}).get("price")
    brent_price = b.get("brent", {}).get("price")
    if dubai_price and brent_price:
        recalc_osps(data, dubai_price, brent_price)
        print(f"\n[3] OSPs recalculated vs Dubai ${dubai_price} / Brent ${brent_price}")
    else:
        print("\n[3] Skipping OSP recalc — missing prices")

    # 5. Push
    data["_updated"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    print("\n[4] Pushing to GitHub...")
    try:
        commit = gh_put(GH_FILE, data, sha, f"prices: auto-update {today}")
        print(f"  Done — commit {commit}")
    except Exception as e:
        print(f"  Push failed: {e}")

if __name__ == "__main__":
    main()
