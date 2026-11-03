"""
Contango Energy — live price snapshot (Brent + WTI) -> data/live.json

One API call per run (both prices come back together), so the free tier
(50 requests/day) is never the limit.

Source: OilPriceAPI  https://docs.oilpriceapi.com/
Required secret / env var: OILPRICEAPI_KEY

Run locally to test:
    OILPRICEAPI_KEY=your_key_here python3 live_update.py
    python3 -m http.server 8000      # then open http://localhost:8000

Editorial rules this script follows:
  - Publishes only what the API reports, with the API's own timestamp, type
    and source label. Nothing is estimated or filled in.
  - Values the API marks "synthetic" (carried forward, not a real quote) are
    never published.
  - If the API fails, the previous live.json is left untouched and the script
    exits non-zero so the GitHub Action shows a red X instead of silently
    pretending everything is fine.
  - If nothing changed since the last run, the file is not rewritten, so no
    empty commits.
"""

import os, sys, json, datetime, urllib.request, urllib.error
from pathlib import Path

API_URL = os.environ.get("OILPRICEAPI_URL", "https://api.oilpriceapi.com/v1/prices/latest")
CODES = {"BRENT_CRUDE_USD": "brent", "WTI_USD": "wti"}
LIVE_PATH = Path("data/live.json")


def fetch_latest(api_key):
    url = API_URL + "?by_code=" + ",".join(CODES)
    req = urllib.request.Request(url, headers={
        "Authorization": "Token " + api_key,
        "User-Agent": "ContangoEnergy/1.0 (+https://contango-energy.com)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def extract_items(resp):
    """The API returns either data.prices[] (several codes) or data{} (one code).
    Accept both so a change in shape doesn't break the run."""
    data = resp.get("data")
    if isinstance(data, dict) and isinstance(data.get("prices"), list):
        return [x for x in data["prices"] if isinstance(x, dict)]
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def build_entry(item):
    """Turn one API item into the small record the website shows. Returns None
    if it isn't usable (no price, or a synthetic carried-forward value)."""
    try:
        price = float(item.get("price"))
    except (TypeError, ValueError):
        return None
    if item.get("synthetic") is True:
        return None
    meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    return {
        "price": round(price, 2),
        "currency": item.get("currency") or "USD",
        # as_of = when the source observed it; fall back to when the API recorded it
        "as_of": item.get("as_of") or item.get("created_at") or item.get("collected_at"),
        "stale": bool(item.get("stale")),
        "type": item.get("type"),
        "source": item.get("source") or meta.get("source") or "OilPriceAPI",
        "code": item.get("code"),
    }


def main():
    api_key = os.environ.get("OILPRICEAPI_KEY", "").strip()
    if not api_key:
        print("ERROR: OILPRICEAPI_KEY not set.", file=sys.stderr)
        sys.exit(1)

    try:
        resp = fetch_latest(api_key)
    except urllib.error.HTTPError as e:
        hint = {401: "key missing/invalid", 429: "rate limit hit"}.get(e.code, "")
        print(f"ERROR: API returned HTTP {e.code} {hint}".strip(), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: API request failed: {e}", file=sys.stderr)
        sys.exit(1)

    existing = {}
    if LIVE_PATH.exists():
        try:
            existing = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    fresh = {}
    for item in extract_items(resp):
        key = CODES.get(item.get("code"))
        if not key:
            continue
        entry = build_entry(item)
        if entry is None:
            print(f"  {key}: skipped (no price or synthetic value)")
            continue
        fresh[key] = entry
        print(f"  {key}: ${entry['price']:.2f}  as_of={entry['as_of']}  stale={entry['stale']}  [{entry['source']}]")

    if not fresh:
        print("ERROR: API answered but contained no usable Brent/WTI price.", file=sys.stderr)
        sys.exit(1)

    # Keep the previous value for any code that didn't come back this time
    merged = {k: existing[k] for k in CODES.values() if isinstance(existing.get(k), dict)}
    merged.update(fresh)

    old_core = {k: existing.get(k) for k in CODES.values()}
    if merged == {k: v for k, v in old_core.items() if v is not None}:
        print("No change since last run - live.json left as is.")
        return

    out = {
        "_note": "Written by live_update.py from OilPriceAPI. as_of is the source's own timestamp (UTC).",
        "_updated": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.update(merged)
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIVE_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {LIVE_PATH}")


if __name__ == "__main__":
    main()
