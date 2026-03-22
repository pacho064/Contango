"""
Contango Energy — monthly OSP differential updater
Run this once a month when NOCs publish their official OSPs (~1st of each month).

Usage:
  python osp_update.py --arabl +2.50 --murban +2.93 --basra +0.65 --kec +0.20 --aheavy -0.95

What to enter:
  These are the DIFFERENTIALS vs Oman/Dubai average published by each NOC.
  e.g. Aramco says "Arab Light Asia = Oman/Dubai +$2.50" → enter --arabl 2.50
  The script stores the differential. The daily updater.py then computes the
  absolute price automatically from live Oman/Dubai.

Where to find the numbers (check these on the 1st–5th of each month):
  Arab Light  → argaam.com/en or arabnews.com (search "Aramco OSP")
  Murban      → adnoc.ae or zawya.com (search "ADNOC Murban OSP")
  Basra       → oil.gov.iq or reuters.com (search "SOMO Basra OSP")
  Kuwait      → kpc.com.kw or mees.com (search "KPC OSP")
  Arab Heavy  → same Aramco release as Arab Light

This script edits data/prices.json directly in your local repo.
After running: git add data/prices.json && git commit -m "OSP: March 2026" && git push
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


OSP_KEYS = {
    "arabl":  "arab_light",
    "murban": "murban",
    "basra":  "basra_medium",
    "kec":    "kuwait_export",
    "aheavy": "arab_heavy",
}

MONTH_NAMES = {
    1:"January", 2:"February", 3:"March", 4:"April",
    5:"May", 6:"June", 7:"July", 8:"August",
    9:"September", 10:"October", 11:"November", 12:"December"
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Update monthly OSP differentials in data/prices.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    p.add_argument("--arabl",  type=float, required=True,  help="Arab Light diff vs Oman/Dubai (e.g. 2.50)")
    p.add_argument("--murban", type=float, required=True,  help="Murban diff vs Oman/Dubai (e.g. 2.93)")
    p.add_argument("--basra",  type=float, required=True,  help="Basra Medium diff vs Oman/Dubai (e.g. 0.65)")
    p.add_argument("--kec",    type=float, required=True,  help="Kuwait Export diff vs Oman/Dubai (e.g. 0.20)")
    p.add_argument("--aheavy", type=float, required=True,  help="Arab Heavy diff vs Oman/Dubai (e.g. -0.95)")
    p.add_argument("--month",  type=str,   default=None,   help="Override month label (e.g. 'April 2026'). Auto-detects if omitted.")
    p.add_argument("--file",   type=str,   default="data/prices.json", help="Path to prices.json")
    p.add_argument("--ttf",   type=float, default=None, help="TTF gas EUR/MWh (manual, optional)")
    p.add_argument("--jkm",   type=float, default=None, help="JKM LNG $/MMBtu (manual, optional)")
    p.add_argument("--urals", type=float, default=None, help="Urals $/bbl (manual, optional)")
    return p.parse_args()


def main():
    args = parse_args()
    path = Path(args.file)

    if not path.exists():
        raise SystemExit(f"File not found: {path}\nRun from the root of your Contango repo.")

    data = json.loads(path.read_text(encoding="utf-8"))

    now = datetime.utcnow()
    # OSP published ~1st of month covers NEXT month's loading
    loading_month = now.month + 1 if now.month < 12 else 1
    loading_year  = now.year if now.month < 12 else now.year + 1
    month_label   = args.month or f"{MONTH_NAMES[loading_month]} {loading_year}"
    today         = now.strftime("%Y-%m-%d")

    inputs = {
        "arabl":  args.arabl,
        "murban": args.murban,
        "basra":  args.basra,
        "kec":    args.kec,
        "aheavy": args.aheavy,
    }

    # Get current Oman/Dubai to show indicative absolute prices
    oman_dubai = data.get("benchmarks", {}).get("oman_dubai", {}).get("price")

    print(f"\nContango OSP updater — {today}")
    print(f"Loading month: {month_label}")
    if oman_dubai:
        print(f"Oman/Dubai spot (live): ${oman_dubai:.2f}")
    else:
        print("Oman/Dubai spot: not available — absolute prices will be computed at next auto-update")
    print()

    osps = data.setdefault("osps", {})

    for short_key, diff in inputs.items():
        json_key = OSP_KEYS[short_key]
        if json_key not in osps:
            osps[json_key] = {}

        osp = osps[json_key]
        osp["differential_vs_omd"] = diff
        osp["for_month"]           = month_label
        osp["updated"]             = today

        # Compute indicative absolute if we have Oman/Dubai
        if oman_dubai is not None:
            absolute = round(oman_dubai + diff, 2)
            osp["price"] = absolute
            sign = "+" if diff >= 0 else ""
            print(f"  {osp.get('grade', json_key):<20} diff: {sign}{diff:.2f}  →  ${absolute:.2f}")
        else:
            sign = "+" if diff >= 0 else ""
            print(f"  {osp.get('grade', json_key):<20} diff: {sign}{diff:.2f}  (absolute: pending next auto-update)")

    # Update metadata
    data["_osp_month"]   = month_label
    data["_osp_updated"] = today

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"\nSaved to {path}")
    print("\nNext steps:")
    print(f"  git add {path}")
    print(f'  git commit -m "OSP: {month_label} differentials"')
    print("  git push")
    print("\nThe daily updater will recompute absolute prices on next run.")


if __name__ == "__main__":
    main(# Optional manual benchmarks
    for arg_name, json_key, label in [
        ("ttf",   "ttf",   "TTF Gas (ICE)"),
        ("jkm",   "jkm",   "JKM LNG (Platts)"),
        ("urals", "urals", "Urals (Argus)"),
    ]:
        val = getattr(args, arg_name)
        if val is not None:
            data["benchmarks"].setdefault(json_key, {}).update({
                "price": val, "updated": today,
                "source": f"{label} — manually entered",
            })
            print(f"  {label}: ${val}")
```

So your monthly command becomes something like:
```
python osp_update.py --arabl 2.50 --murban 2.93 --basra 0.65 --kec 0.20 --aheavy -0.95 --ttf 48.30 --jkm 24.70 --urals 52.40)
