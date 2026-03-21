#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


def parser():
    p = argparse.ArgumentParser(
        description="Update Contango core5 values in data/core5.json"
    )
    p.add_argument("--brent", type=float, required=True)
    p.add_argument("--arabl", type=float, required=True)
    p.add_argument("--murban", type=float, required=True)
    p.add_argument("--omd", type=float, required=True)
    p.add_argument("--basram", type=float, required=True)
    p.add_argument("--kec", type=float, required=True)
    p.add_argument("--event-date", type=str, default=None)
    p.add_argument("--event-name", type=str, default=None)
    return p


def main():
    args = parser().parse_args()
    data_path = Path("data/core5.json")
    if not data_path.exists():
        raise SystemExit(f"Missing data file: {data_path}")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    by_key = {item["key"]: item for item in data["core5"]}

    by_key["lead"]["currentValue"] = args.arabl
    by_key["lead"]["refValue"] = args.brent
    by_key["murban"]["currentValue"] = args.murban
    by_key["omd"]["currentValue"] = args.omd
    by_key["basra"]["currentValue"] = args.basram
    by_key["kec"]["currentValue"] = args.kec

    if args.event_date:
        data["eventBaseline"]["date"] = args.event_date
    if args.event_name:
        data["eventBaseline"]["name"] = args.event_name

    data["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%d")
    data_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    spread = args.arabl - args.brent
    print("Updated data/core5.json")
    print(f"Arab Light vs Brent spread: {spread:.2f} $/bbl")


if __name__ == "__main__":
    main()
