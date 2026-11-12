"""
Contango Energy — live oil price snapshot -> data/live.json

  Core     Brent + WTI           one API call, every run (every 30 min)
  Regional Dubai, OPEC basket,   one separate API call, every 4 hours (these
           WCS (+ any you add)   move at business-day cadence, not tick by tick)

Total is roughly 38 calls/day against the free tier's 50/day.

Source: OilPriceAPI  https://docs.oilpriceapi.com/
Required secret / env var: OILPRICEAPI_KEY

Run locally to test:
    OILPRICEAPI_KEY=your_key python3 live_update.py --all
    python3 -m http.server 8000      # then open http://localhost:8000

Other commands:
    python3 live_update.py --list-codes          show which price codes your key can see
    python3 live_update.py --retry-unavailable   re-try codes previously marked unavailable
Add more regional grades without editing code:
    EXTRA_CODES="CODE_ONE=Label One,CODE_TWO=Label Two" python3 live_update.py --all

Editorial rules this script follows:
  - Publishes only what the API reports, with the API's own timestamp, type
    and source label. Nothing is estimated, converted or filled in.
  - Values the API marks "synthetic" (carried forward, not a real quote) are
    never published.
  - Core failure (Brent/WTI) -> exit non-zero so the GitHub Action turns red
    and the previous live.json is left untouched.
  - Regional failure never costs you Brent/WTI: it is logged as a warning, and
    a code the API rejects (unknown or not on your plan) is remembered in
    live.json under "regional_unavailable" so it is not requested again.
  - Nothing changed since the last run -> the file is not rewritten.
"""

import os, sys, json, datetime, urllib.request, urllib.error
from pathlib import Path

LATEST_URL = os.environ.get("OILPRICEAPI_URL", "https://api.oilpriceapi.com/v1/prices/latest")
API_BASE = LATEST_URL.split("/v1/")[0]

CORE = {"BRENT_CRUDE_USD": "brent", "WTI_USD": "wti"}

# Codes confirmed in OilPriceAPI's public docs. Whether your plan includes each
# one is checked on the first run and remembered (see regional_unavailable).
REGIONAL = {
    "DUBAI_CRUDE_USD": "Dubai (Fateh)",
    "OPEC_BASKET_USD": "OPEC Reference Basket",
    "WCS_CRUDE_USD": "Western Canadian Select",
}
for _pair in os.environ.get("EXTRA_CODES", "").split(","):
    _code, _, _label = _pair.partition("=")
    if _code.strip():
        REGIONAL[_code.strip()] = _label.strip() or _code.strip()

REGIONAL_EVERY_HOURS = 4
REJECTED = (400, 402, 403, 404)   # "this code isn't valid / isn't on your plan"
LIVE_PATH = Path("data/live.json")


class ApiError(Exception):
    def __init__(self, status, body=""):
        super().__init__(f"HTTP {status} {body}".strip())
        self.status = status


def api_get(url, api_key):
    req = urllib.request.Request(url, headers={
        "Authorization": "Token " + api_key,
        "User-Agent": "ContangoEnergy/1.0 (+https://contango-energy.com)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, e.read()[:150].decode("utf-8", "ignore"))


def extract_items(resp):
    """The API returns either data.prices[] (several codes) or data{} (one code).
    Accept both so a change in shape doesn't break the run."""
    data = resp.get("data")
    if isinstance(data, dict) and isinstance(data.get("prices"), list):
        return [x for x in data["prices"] if isinstance(x, dict)]
    if isinstance(data, dict) and "price" in data:
        return [data]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def fetch_codes(codes, api_key):
    resp = api_get(LATEST_URL + "?by_code=" + ",".join(codes), api_key)
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    withheld = [m.get("code") for m in (data.get("missing") or []) if isinstance(m, dict)]
    return extract_items(resp), withheld


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
        "unit": item.get("unit"),
        # as_of = when the source observed it; fall back to record dates
        "as_of": item.get("as_of") or item.get("source_date") or item.get("created_at") or item.get("collected_at"),
        "stale": bool(item.get("stale")),
        "type": item.get("type"),
        "data_status": item.get("data_status"),
        "source": item.get("source") or meta.get("source") or "OilPriceAPI",
        "code": item.get("code"),
    }


def regional_due(now):
    """Scheduled runs fetch regional grades once every 4 hours (the first run of that hour)."""
    return now.hour % REGIONAL_EVERY_HOURS == 0 and now.minute < 30


def load_existing():
    if LIVE_PATH.exists():
        try:
            return json.loads(LIVE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def do_core(api_key, existing):
    try:
        items, _ = fetch_codes(list(CORE), api_key)
    except ApiError as e:
        hint = {401: "key missing/invalid", 429: "rate limit hit"}.get(e.status, "")
        print(f"ERROR: core request failed: {e} {hint}".strip(), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: core request failed: {e}", file=sys.stderr)
        sys.exit(1)

    fresh = {}
    for item in items:
        key = CORE.get(item.get("code"))
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
    merged = {k: existing[k] for k in CORE.values() if isinstance(existing.get(k), dict)}
    merged.update(fresh)
    return merged


def do_regional(api_key, existing, retry_unavailable):
    """Returns (list_of_entries, unavailable_dict). Never raises: regional
    problems must not cost us the core prices."""
    prev = [e for e in (existing.get("regional") or []) if isinstance(e, dict)]
    unavailable = {} if retry_unavailable else dict(existing.get("regional_unavailable") or {})
    wanted = [c for c in REGIONAL if c not in unavailable]
    if not wanted:
        print("  regional: nothing to request (all codes marked unavailable; use --retry-unavailable)")
        return prev, unavailable

    items = []
    try:
        got, withheld = fetch_codes(wanted, api_key)
        items += got
        for c in withheld:
            print(f"  regional: {c} withheld by API this time")
    except ApiError as e:
        if e.status == 429:
            print(f"  WARNING regional: rate limit hit, keeping previous values", file=sys.stderr)
            return prev, unavailable
        if e.status in REJECTED and len(wanted) > 1:
            # One bad code spoils a multi-code request: probe each on its own and remember failures.
            print(f"  regional: {e}; probing codes one by one")
            for c in wanted:
                try:
                    got, _ = fetch_codes([c], api_key)
                    items += got
                except ApiError as e2:
                    if e2.status in REJECTED:
                        unavailable[c] = f"HTTP {e2.status}"
                        print(f"  regional: {c} not available ({e2.status}) - will skip it from now on")
                    elif e2.status == 429:
                        print("  WARNING regional: rate limit hit while probing", file=sys.stderr)
                        break
                except Exception as e2:
                    print(f"  WARNING regional: {c}: {e2}", file=sys.stderr)
        elif e.status in REJECTED:
            unavailable[wanted[0]] = f"HTTP {e.status}"
            print(f"  regional: {wanted[0]} not available ({e.status}) - will skip it from now on")
        else:
            print(f"  WARNING regional: {e}", file=sys.stderr)
            return prev, unavailable
    except Exception as e:
        print(f"  WARNING regional: {e}", file=sys.stderr)
        return prev, unavailable

    fresh = {}
    for item in items:
        code = item.get("code")
        if code not in REGIONAL:
            continue
        entry = build_entry(item)
        if entry is None:
            print(f"  {code}: skipped (no price or synthetic value)")
            continue
        entry["label"] = REGIONAL[code]
        fresh[code] = entry
        print(f"  {code}: ${entry['price']:.2f}  as_of={entry['as_of']}  [{entry['source']}]")

    old = {e.get("code"): e for e in prev}
    out = []
    for code in REGIONAL:                      # keep configured order
        e = fresh.get(code) or old.get(code)
        if e and code not in unavailable:
            out.append(e)
    return out, unavailable


def list_codes(api_key):
    """Helper: show what the API says your key can see, so you can find codes for
    Urals, Bonny Light, Mars etc. We print the raw JSON rather than guess its shape."""
    for path in ("/v1/commodities", "/v1/prices/codes"):
        try:
            data = api_get(API_BASE + path, api_key)
        except ApiError as e:
            print(f"{path}: {e}")
            continue
        text = json.dumps(data, indent=1)
        print(f"{path} (first 6000 characters):\n{text[:6000]}")
        return
    print("Could not read a code catalog. See https://docs.oilpriceapi.com/")


def main():
    args = sys.argv[1:]
    api_key = os.environ.get("OILPRICEAPI_KEY", "").strip()
    if not api_key:
        print("ERROR: OILPRICEAPI_KEY not set.", file=sys.stderr)
        sys.exit(1)
    if "--list-codes" in args:
        list_codes(api_key)
        return

    existing = load_existing()
    now = datetime.datetime.now(datetime.timezone.utc)

    core = do_core(api_key, existing)

    regional, unavailable = existing.get("regional") or [], existing.get("regional_unavailable") or {}
    if "--all" in args or regional_due(now):
        print("Regional grades:")
        regional, unavailable = do_regional(api_key, existing, "--retry-unavailable" in args)
    else:
        print("Regional grades: not due this run (every 4 hours; use --all to force)")

    new_body = dict(core)
    if regional:
        new_body["regional"] = regional
    if unavailable:
        new_body["regional_unavailable"] = unavailable

    old_body = {k: v for k, v in existing.items() if not k.startswith("_")}
    if new_body == old_body:
        print("No change since last run - live.json left as is.")
        return

    out = {
        "_note": "Written by live_update.py from OilPriceAPI. as_of is the source's own timestamp (UTC).",
        "_updated": now.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.update(new_body)
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIVE_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {LIVE_PATH}")


if __name__ == "__main__":
    main()
