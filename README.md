# Contango

**Open-source energy market intelligence.**

> *Contango* — when the futures price exceeds the spot price. The market is pricing in more than it admits.

This platform makes that gap visible: between headline benchmarks (Brent, WTI) and the local Official Selling Prices that Middle East producers actually trade at, between the pipeline capacity that's cited as a strategic bypass and the port capacity that makes that argument structurally weak, between what gets reported and what's actually moving.

---

## What it does

- **Global benchmark bar** — Brent, WTI, LNG JKM, TTF, RBOB, Henry Hub with live % change, always visible
- **Local OSP premium strip** — real-time differential between Oman, Murban, Arab Light, Dubai, Basra, Qatar Marine and the Brent benchmark
- **Interactive regional map** with five layers:
  - Local prices — hover any country for OSP, production, grade, buyers, geo-risk
  - Geo-risk — risk-scored choropleth across the region
  - Ports & capacity — size-coded terminals with utilisation alerts, hover for capacity detail
  - Pipelines — active, disrupted, and decommissioned routes with the Yanbu constraint callout
  - Export flows — animated flow arcs to major consumer regions
- **Price history chart** with annotated conflict event markers
- **OPEC+ quota vs actual output** — who's compliant, who isn't
- **Port utilisation panel** — colour-coded near-capacity alerts
- **Breaking intelligence feed** — sourced from Reuters, MEES, ministry feeds
- **Light + dark mode**

## The Yanbu argument

Saudi Arabia's East-West pipeline is frequently cited as the solution to Strait of Hormuz vulnerability. Contango makes the structural counter-argument visible:

- Pipeline capacity: **5M bbl/d** (Abqaiq → Yanbu)
- Yanbu port export capacity: **~1.8M bbl/d**
- Houthi operations at Bab el-Mandeb then add a **second chokepoint** to this already constrained route

The pipeline is not the bottleneck. The port is. This is the argument the platform is built to surface.

---

## Deploy

**Netlify (30 seconds):**
Drag the folder to [netlify.com/drop](https://app.netlify.com/drop)

**Vercel:**
```bash
npx vercel --prod
```

**GitHub Pages:**
```bash
git init && git add . && git commit -m "init contango"
gh repo create contango --public --push --source=.
# Enable Pages: Settings → Pages → Deploy from main branch
```

**Custom domain:** point `contango.watch` or `contango.energy` DNS to your host.

---

## Connecting real data

Current version uses a simulated price feed (ticks every 4.2s). To wire real data, replace the `PRICES` / `BENCH` arrays with API calls:

| Data point | Source | Endpoint |
|------------|--------|----------|
| Brent / WTI / Henry Hub | EIA | `api.eia.gov/v2/petroleum` |
| LNG JKM / Platts assessments | S&P Global | `developer.spglobal.com` |
| Oman crude OSP | Dubai Mercantile Exchange | `dubaimerc.com/api` |
| Breaking news | Reuters | `reuters.com/pf/api/v3` |
| Port AIS / tanker positions | MarineTraffic | `marinetraffic.com/api` |
| OPEC+ production | OPEC Secretariat | `opec.org/basket` |

See `/docs/data-connectors.md` for full integration guide (in progress).

---

## Roadmap

- [ ] Real DME + EIA API integration
- [ ] Tanker shadow fleet tracker (AIS data)
- [ ] Conflict event database (auto-annotates price history)
- [ ] Alert system — price threshold + chokepoint event notifications
- [ ] Embeddable price widget for press/research
- [ ] Additional regions: West Africa, Caspian, North Sea
- [ ] Mobile layout

## Contributing

Contango is intentionally simple — a single `index.html` deployable anywhere. Fork it, extend it, send a PR.

**Priority contributions:**
- Real-time data connector implementations
- Additional producing country OSPs (Kazakhstan, Nigeria, Angola, Libya)
- Historical conflict event database (JSON format)
- Tanker AIS integration

## License

MIT — free to use, fork, embed, build on.

---

## Why "Contango"

In commodity markets, contango describes the condition where the futures price exceeds the current spot price — the market is pricing in anticipated disruption, scarcity, or uncertainty. It's the gap between what's happening now and what the market believes will happen.

This platform is built around a parallel gap: between the benchmark prices that dominate financial media (Brent, WTI) and the local Official Selling Prices that producers in the Middle East actually trade at — prices that respond faster to geopolitical reality, port constraints, and demand-side shifts than any exchange-listed contract.

When Oman crude trades at $161 while Brent sits at $138, that $23 premium isn't noise. It's signal.
