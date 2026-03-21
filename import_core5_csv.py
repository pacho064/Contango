#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


REQUIRED_KEYS = {"lead", "murban", "omd", "basra", "kec"}


def to_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    return float(s)


def parse_args():
    p = argparse.ArgumentParser(description="Import core5 values from CSV into data/core5.json")
    p.add_argument("--csv", default="data/core5_template.csv", help="Path to source CSV")
    p.add_argument("--json", default="data/core5.json", help="Path to destination JSON")
    p.add_argument("--event-date", default=None, help="Optional YYYY-MM-DD")
    p.add_argument("--event-name", default=None, help="Optional event name override")
    return p.parse_args()


def main():
    args = parse_args()
    csv_path = Path(args.csv)
    json_path = Path(args.json)

    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")
    if not json_path.exists():
        raise SystemExit(f"JSON file not found: {json_path}")

    rows = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row.get("series_key") or "").strip()
            if not key:
                continue
            rows.append(
                {
                    "series_key": key,
                    "current_value": to_float(row.get("current_value")),
                    "ref_value": to_float(row.get("ref_value")),
                    "feb1_value": to_float(row.get("feb1_value")),
                    "source": (row.get("source") or "").strip(),
                    "source_url": (row.get("source_url") or "").strip(),
                }
            )

    found_keys = {r["series_key"] for r in rows}
    missing = REQUIRED_KEYS - found_keys
    if missing:
        raise SystemExit(f"CSV missing required series_key rows: {', '.join(sorted(missing))}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    by_key = {item["key"]: item for item in data["core5"]}

    for row in rows:
        key = row["series_key"]
        if key not in by_key:
            continue
        item = by_key[key]
        if row["current_value"] is not None:
            item["currentValue"] = row["current_value"]
        if row["feb1_value"] is not None:
            item["feb1Value"] = row["feb1_value"]
        if row["source"]:
            item["source"] = row["source"]
        if "source_url" in row:
            item["sourceUrl"] = row["source_url"]
        if key == "lead" and row["ref_value"] is not None:
            item["refValue"] = row["ref_value"]

    if args.event_date:
        data["eventBaseline"]["date"] = args.event_date
    if args.event_name:
        data["eventBaseline"]["name"] = args.event_name

    data["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%d")
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    lead = by_key["lead"]
    spread = float(lead.get("currentValue", 0)) - float(lead.get("refValue", 0))
    print(f"Imported CSV: {csv_path}")
    print(f"Updated JSON: {json_path}")
    print(f"Arab Light vs Brent spread: {spread:.2f} $/bbl")


if __name__ == "__main__":
    main()
