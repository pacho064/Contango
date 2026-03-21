#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const dataPath = path.resolve(process.cwd(), "data/core5.json");

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      out[key] = true;
      continue;
    }
    out[key] = next;
    i += 1;
  }
  return out;
}

function toNum(v, label) {
  const n = Number(v);
  if (!Number.isFinite(n)) throw new Error(`Invalid numeric value for ${label}: ${v}`);
  return n;
}

function usage() {
  console.log(`Usage:
  node scripts/update-core5.mjs --brent 84.2 --arabl 86.1 --murban 87.3 --omd 85.6 --basram 83.9 --kec 84.4

Optional:
  --event-date YYYY-MM-DD
  --event-name "US-Iran war volatility baseline"
`);
}

function main() {
  if (!fs.existsSync(dataPath)) {
    throw new Error(`Missing data file: ${dataPath}`);
  }

  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return;
  }

  const required = ["brent", "arabl", "murban", "omd", "basram", "kec"];
  const missing = required.filter((k) => !(k in args));
  if (missing.length > 0) {
    usage();
    throw new Error(`Missing required flags: ${missing.map((m) => `--${m}`).join(", ")}`);
  }

  const brent = toNum(args.brent, "brent");
  const arabl = toNum(args.arabl, "arabl");
  const murban = toNum(args.murban, "murban");
  const omd = toNum(args.omd, "omd");
  const basram = toNum(args.basram, "basram");
  const kec = toNum(args.kec, "kec");

  const raw = fs.readFileSync(dataPath, "utf8");
  const data = JSON.parse(raw);
  const currentDate = new Date().toISOString().slice(0, 10);

  if (args["event-date"]) data.eventBaseline.date = args["event-date"];
  if (args["event-name"]) data.eventBaseline.name = String(args["event-name"]);

  const byKey = new Map(data.core5.map((s) => [s.key, s]));
  byKey.get("lead").currentValue = arabl;
  byKey.get("lead").refValue = brent;
  byKey.get("murban").currentValue = murban;
  byKey.get("omd").currentValue = omd;
  byKey.get("basra").currentValue = basram;
  byKey.get("kec").currentValue = kec;

  data.lastUpdated = currentDate;
  fs.writeFileSync(dataPath, `${JSON.stringify(data, null, 2)}\n`, "utf8");

  const spread = arabl - brent;
  console.log("Updated data/core5.json");
  console.log(`Arab Light vs Brent spread: ${spread.toFixed(2)} $/bbl`);
  console.log(`Updated date: ${currentDate}`);
}

main();
