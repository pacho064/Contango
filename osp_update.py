"""
Contango Energy — monthly OSP differential updater
Run once a month when NOCs publish OSPs (~1st of each month).

Usage:
  python osp_update.py --arabl 2.50 --murban 2.93 --basra 0.65 --kec 0.20 --aheavy -0.95

Optional gas/other benchmarks:
  --ttf 48.30 --jkm 24.70 --urals 52.40

Where to find the numbers:
  Arab Light  → argaam.com or arabnews.com (search "Aramco OSP")
  Murban      → zawya.com or adnoc.ae
  Basra       → oil.gov.iq or reuters.com (search "SOMO Basra OSP")
  Kuwait      → kpc.com.kw
  Arab Heavy  → same Aramco release as Arab Light
"""

import argparse, json
from datetime import datetime
from pathlib import Path

OSP_KEYS = {
    "arabl":  "arab_light",
    "murban": "murban",
    "basra":  "basra_medium",
    "kec":    "kuwait_export",
    "aheavy": "arab_heavy",
}
MONTHS = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
          7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}

def parse_args():
    p = argparse.ArgumentParser(description="Update monthly OSP differentials")
    p.add_argument("--arabl",  type=float, required=True)
    p.add_argument("--murban", type=float, required=True)
    p.add_argument("--basra",  type=float, required=True)
    p.add_argument("--kec",    type=float, required=True)
    p.add_argument("--aheavy", type=float, required=True)
    p.add_argument("--ttf",    type=float, default=None)
    p.add_argument("--jkm",    type=float, default=None)
    p.add_argument("--urals",  type=float, default=None)
    p.add_argument("--month",  type=str,   default=None)
    p.add_argument("--file",   type=str,   default="data/prices.json")
    return p.parse_args()

def main():
    args = parse_args()
    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}\nRun from the root of your Contango repo.")

    data  = json.loads(path.read_text(encoding="utf-8"))
    now   = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")

    lm = now.month + 1 if now.month < 12 else 1
    ly = now.year if now.month < 12 else now.year + 1
    month_label = args.month or f"{MONTHS[lm]} {ly}"

    oman_dubai = data.get("benchmarks", {}).get("oman_dubai", {}).get("price")
    print(f"\nContango OSP updater — {today}")
    print(f"Loading month: {month_label}")
    print(f"Oman/Dubai spot: {'$'+str(oman_dubai) if oman_dubai else 'not available'}\n")

    osps = data.setdefault("osps", {})
    inputs = {"arabl":args.arabl,"murban":args.murban,"basra":args.basra,
              "kec":args.kec,"aheavy":args.aheavy}

    for short_key, diff in inputs.items():
        json_key = OSP_KEYS[short_key]
        osp = osps.setdefault(json_key, {})
        osp["differential_vs_omd"] = diff
        osp["for_month"]           = month_label
        osp["updated"]             = today
        if oman_dubai is not None:
            osp["price"] = round(oman_dubai + diff, 2)
        sign = "+" if diff >= 0 else ""
        price_str = f"  → ${osp['price']:.2f}" if oman_dubai else ""
        print(f"  {osp.get('grade', json_key):<20} diff: {sign}{diff:.2f}{price_str}")

    # Optional manual benchmarks
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

    data["_osp_month"]   = month_label
    data["_osp_updated"] = today
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"\nSaved to {path}")
    print(f"  git add {path}")
    print(f'  git commit -m "OSP: {month_label} differentials"')
    print("  git push")

if __name__ == "__main__":
    main()
