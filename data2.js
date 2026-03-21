/* Contango v3.0 · 20 March 2026 · github.com/pacho064/Contango
/* ================================================================
   CONTANGO — Content & Data Layer
   Edit this file to update all content across the site.
   No design knowledge required.
   ================================================================ */

window.CONTANGO = {

/* ── Site meta ─────────────────────────────────────────────── */
meta:{
  version:'v3.0',
  updated:'20 March 2026',
  githubUrl:'https://github.com/pacho064/Contango',
},

/* ── Global benchmarks ─────────────────────────────────────── */
benchmarks:[
  {sym:'BRENT', name:'Brent crude (ICE)',      base:138.40, dec:2, note:'Global reference benchmark'},
  {sym:'WTI',   name:'WTI Cushing (CME)',      base:134.20, dec:2, note:'US benchmark'},
  {sym:'JKM',   name:'LNG JKM Asia',           base:24.70,  dec:2, note:'Asian LNG spot price'},
  {sym:'TTF',   name:'TTF Natural Gas',        base:48.30,  dec:2, note:'European gas benchmark'},
  {sym:'HH',    name:'Henry Hub (US gas)',     base:2.18,   dec:3, note:'US natural gas'},
  {sym:'RBOB',  name:'RBOB Gasoline',          base:3.84,   dec:3, note:'US gasoline futures'},
  {sym:'URALS', name:'Urals (Russia)',         base:108.50, dec:2, note:'Discounted from Brent due to sanctions — trades at ~$28-30 discount'},
  {sym:'ESPO',  name:'ESPO Blend (Russia→China)', base:122.80, dec:2, note:'Far East Russian crude, less discounted than Urals'},
  {sym:'DAQING',name:'Daqing (China domestic)',base:136.80, dec:2, note:'Chinese domestic crude reference price (CNOOC/PetroChina)'},
],

/* ── Middle East local OSPs ─────────────────────────────────── */
localOSPs:[
  {sym:'OMAN',    name:'Oman crude',        grade:'Sour medium', base:161.40, dec:2, country:'Oman',         exchange:'DME',   source:'Dubai Mercantile Exchange',   src_updated:'1 Mar 2026'},
  {sym:'MURBAN',  name:'Murban',            grade:'Sweet light', base:163.20, dec:2, country:'UAE',          exchange:'ADNOC', source:'ADNOC OSP release',           src_updated:'1 Mar 2026'},
  {sym:'DUBAI',   name:'Dubai spot',        grade:'Sour medium', base:159.80, dec:2, country:'UAE',          exchange:'Platts',source:'S&P Global Platts assessment', src_updated:'20 Mar 2026'},
  {sym:'ARAB L',  name:'Arab Light',        grade:'Sour light',  base:162.10, dec:2, country:'Saudi Arabia', exchange:'Aramco',source:'Saudi Aramco OSP',             src_updated:'1 Mar 2026'},
  {sym:'ARAB H',  name:'Arab Heavy',        grade:'Sour heavy',  base:155.40, dec:2, country:'Saudi Arabia', exchange:'Aramco',source:'Saudi Aramco OSP',             src_updated:'1 Mar 2026'},
  {sym:'BASRA L', name:'Basra Light',       grade:'Sour medium', base:158.20, dec:2, country:'Iraq',         exchange:'SOMO',  source:'SOMO Iraq official price',     src_updated:'1 Mar 2026'},
  {sym:'BASRA H', name:'Basra Heavy',       grade:'Sour heavy',  base:153.90, dec:2, country:'Iraq',         exchange:'SOMO',  source:'SOMO Iraq official price',     src_updated:'1 Mar 2026'},
  {sym:'QATAR M', name:'Qatar Marine',      grade:'Sour medium', base:158.60, dec:2, country:'Qatar',        exchange:'QP',    source:'QatarEnergy OSP',             src_updated:'1 Mar 2026'},
  {sym:'KEC',     name:'Kuwait Export',     grade:'Sour medium', base:157.80, dec:2, country:'Kuwait',       exchange:'KPC',   source:'Kuwait Petroleum Corp OSP',    src_updated:'1 Mar 2026'},
  {sym:'MURBAN2', name:'Upper Zakum',       grade:'Sour medium', base:160.40, dec:2, country:'UAE',          exchange:'ADNOC', source:'ADNOC OSP release',           src_updated:'1 Mar 2026'},
],

/* ── Commodities ───────────────────────────────────────────── */
commodities:[
  {sym:'GOLD',  name:'Gold XAU/USD',         base:2618,  dec:0},
  {sym:'WHEAT', name:'Wheat CBOT $/bu',       base:6.12,  dec:2},
  {sym:'BDI',   name:'Baltic Dry Index',      base:1842,  dec:0},
  {sym:'SUEZ',  name:'Suez Canal toll $/vessel', base:410, dec:0},
],

/* ── Intelligence feed ─────────────────────────────────────── */
/* Tags: price | flow | infrastructure | risk | opec */
intel:[
  {
    src:'Reuters Energy',col:'#1F5A94',tag:'risk',tagCol:'#1F5A94',tagBg:'#EBF3FC',
    hl:'Houthi forces report drone strike on commercial tanker south of Aden — Cape of Good Hope rerouting adding ~14 days transit, approximately $1.2M additional voyage cost',
    why:'Sustained Bab el-Mandeb disruption is structurally raising freight costs and increasing Asian LNG premiums. It also removes one of two viable Red Sea routes for Yanbu exports.',
    time:'8 min ago',region:'Red Sea'
  },
  {
    src:'MEES',col:'#2E7D5A',tag:'infrastructure',tagCol:'#2E7D5A',tagBg:'#EAF6F1',
    hl:"Saudi Arabia's East-West pipeline operating at 38% of 5M bbl/d capacity — Yanbu terminal bottleneck confirmed as binding constraint, limiting pipeline's value as Hormuz bypass",
    why:'This confirms the structural argument: the pipeline is not the binding constraint. Yanbu port capacity (1.8M bbl/d) is. Even full pipeline utilisation cannot substitute Hormuz at scale.',
    time:'26 min ago',region:'Saudi Arabia'
  },
  {
    src:'ADNOC',col:'#C58B2A',tag:'price',tagCol:'#C58B2A',tagBg:'#FDF5E6',
    hl:'UAE confirms Murban OSP for April loading: $163.20/bbl — premium to Brent at +$24.80, strongest differential recorded since Q2 2024',
    why:'Murban premium reflects tight sour crude supply and sustained Asian demand for lighter Gulf grades. The gap to Brent has widened by ~$4 since the start of the Red Sea crisis.',
    time:'52 min ago',region:'UAE'
  },
  {
    src:'Iraq SOMO',col:'#B85042',tag:'flow',tagCol:'#B85042',tagBg:'#FDF0EE',
    hl:'Basra export delays extend to 3 days — 14 vessels at anchor outside Khor al-Amaya terminal, fog conditions cited alongside persistent berth congestion',
    why:'Basra SPM is operating at 94% utilisation. This structural near-capacity condition means any weather event cascades into multi-day backlogs with material impact on Iraqi revenues.',
    time:'1h 19m ago',region:'Iraq'
  },
  {
    src:'EIA Weekly',col:'#2E7D5A',tag:'price',tagCol:'#2E7D5A',tagBg:'#EAF6F1',
    hl:'US commercial crude inventories draw 3.2M barrels — Cushing stocks at 5-year seasonal low, narrowing the window for WTI-Brent spread compression',
    why:'Tight Cushing stocks support WTI prices but the spread to Brent remains historically wide at $4.20. This reflects regional dynamics rather than global balance shifts.',
    time:'2h 04m ago',region:'United States'
  },
  {
    src:'Reuters Energy',col:'#1F5A94',tag:'risk',tagCol:'#1F5A94',tagBg:'#EBF3FC',
    hl:'Iran crude exports estimated at 1.8M bbl/d in February via shadow fleet — primarily Shandong independent refiners per satellite AIS tracking',
    why:'Shadow fleet volumes near pre-2022 levels effectively create a parallel market that suppresses the headline impact of sanctions. Iran crude trades at $28-32 discount to Brent.',
    time:'3h 37m ago',region:'Iran'
  },
  {
    src:'S&P Global',col:'#6B7C93',tag:'price',tagCol:'#6B7C93',tagBg:'#F0F3F7',
    hl:'Oman crude premium to Brent widens to +$23/bbl — Asian refiners accelerating sour barrel procurement amid reduced Iranian availability and sanctions uncertainty',
    why:'Oman and Dubai are the effective pricing benchmarks for Asian sour crude. The widening premium reflects real demand pressure that Brent cannot capture.',
    time:'4h 22m ago',region:'Middle East'
  },
  {
    src:'OPEC Secretariat',col:'#1F5A94',tag:'opec',tagCol:'#1F5A94',tagBg:'#EBF3FC',
    hl:'JMMC recommends maintaining current production trajectory through Q2 2026 — full ministerial review scheduled next month',
    why:'Stable quota maintenance keeps supply discipline intact, but Iraq (+0.5M bbl/d over quota) and UAE (+0.5M) overproduction continue to create compliance tensions within OPEC+.',
    time:'5h 02m ago',region:'OPEC+'
  },
  {
    src:'Argus Media',col:'#6B7C93',tag:'price',tagCol:'#6B7C93',tagBg:'#F0F3F7',
    hl:'Russian Urals crude trading at $108.50/bbl as of 19 March — discount to Brent narrows to $29.90 as Indian refinery demand absorbs available volumes',
    why:"India now accounts for ~40% of Russian crude imports. The narrowing discount reflects tight Asian refinery capacity rather than sanctions erosion. Russia's shadow fleet insurance costs remain elevated.",
    time:'6h 15m ago',region:'Russia'
  },
  {
    src:'Al-Monitor',col:'#C58B2A',tag:'risk',tagCol:'#C58B2A',tagBg:'#FDF5E6',
    hl:'Kurdish Regional Government pipeline export dispute with Baghdad shows no resolution — Kirkuk-Ceyhan exports remain at <200k bbl/d vs rated capacity of 1.6M bbl/d',
    why:'The prolonged KRG-Baghdad dispute is a structural under-utilisation of northern Iraq export capacity. The pipeline ran at 12% of capacity in February.',
    time:'7h 44m ago',region:'Iraq'
  },
],

/* ── OPEC+ output ─────────────────────────────────────────── */
opec:[
  {n:'Saudi Arabia', q:10.0, a:10.2, unit:'M bbl/d', note:'Broadly compliant. Minor overage within JMMC tolerance.'},
  {n:'Russia',       q:9.0,  a:9.2,  unit:'M bbl/d', note:'Overproduction reported; compensatory cuts pledged but not fully implemented.'},
  {n:'Iraq',         q:4.0,  a:4.5,  unit:'M bbl/d', note:'Consistent overproduction. Baghdad cites infrastructure constraints preventing faster compliance.'},
  {n:'UAE',          q:3.2,  a:3.7,  unit:'M bbl/d', note:'Overproduction — UAE has requested a higher baseline quota in ongoing OPEC+ negotiations.'},
  {n:'Kuwait',       q:2.7,  a:2.9,  unit:'M bbl/d', note:'Moderate overage. Compensatory cuts pledged for Q2.'},
  {n:'Iran',         q:null, a:3.0,  unit:'M bbl/d', note:'Exempt from quota due to sanctions. Shadow fleet estimate only.'},
  {n:'Venezuela',    q:0.9,  a:0.8,  unit:'M bbl/d', note:'Under quota due to infrastructure degradation, not voluntary compliance.'},
  {n:'Nigeria',      q:1.5,  a:1.3,  unit:'M bbl/d', note:'Under quota due to ongoing pipeline sabotage and investment shortfall.'},
  {n:'Libya',        q:null, a:1.2,  unit:'M bbl/d', note:'Exempt from quota. Production volatile due to political instability.'},
  {n:'Kazakhstan',   q:1.7,  a:2.0,  unit:'M bbl/d', note:'Persistent overproduction — Tengizchevroil expansion driving output beyond OPEC+ commitments.'},
],
opec_source:'OPEC Secretariat JMMC communiqué + Reuters output survey. Actuals are estimates compiled from multiple sources. Updated monthly.',
opec_updated:'March 2026',

/* ── Ports ─────────────────────────────────────────────────── */
ports:[
  {id:'rt',  n:'Ras Tanura',    c:'Saudi Arabia', lon:50.17, lat:26.65, t:'export',   cap:6.5, util:88, note:"World's largest crude export terminal. East coast only — no Red Sea access. The core Hormuz dependency.", source:'Port Authority + IEA'},
  {id:'ju',  n:'Jubail',        c:'Saudi Arabia', lon:49.66, lat:27.00, t:'export',   cap:2.2, util:72, note:'Refined products and petrochemicals. East coast. Separate from crude exports.', source:'Saudi Aramco disclosures'},
  {id:'yn',  n:'Yanbu',         c:'Saudi Arabia', lon:38.05, lat:24.08, t:'export',   cap:1.8, util:61, note:'Red Sea terminal. East-West pipeline delivers 5M bbl/d capacity — but port can only export 1.8M bbl/d. The binding constraint in the bypass argument.', source:'IEA + Aramco'},
  {id:'ja',  n:'Jebel Ali',     c:'UAE',          lon:55.07, lat:24.98, t:'export',   cap:3.5, util:79, note:"UAE's primary export hub. Largest port in the Middle East by container and crude volume.", source:'Dubai Ports World'},
  {id:'fj',  n:'Fujairah',      c:'UAE',          lon:56.35, lat:25.13, t:'export',   cap:1.4, util:85, note:'Key bunkering hub east of Hormuz. Strategic bypass terminal receiving ADCO pipeline crude. Growing volumes since 2024.', source:'Fujairah Oil Industry Zone'},
  {id:'ka',  n:'Khor al-Amaya', c:'Iraq',         lon:48.78, lat:29.98, t:'export',   cap:1.8, util:91, note:'Iraq primary offshore terminal. Currently 3-day loading backlog. Near structural capacity ceiling.', source:'SOMO Iraq'},
  {id:'bs',  n:'Basra SPM',     c:'Iraq',         lon:48.83, lat:29.72, t:'export',   cap:2.0, util:94, note:'Single Point Mooring. Iraq second terminal. At operational ceiling — structural bottleneck constraining revenue growth.', source:'SOMO Iraq'},
  {id:'aden',n:'Aden',          c:'Yemen',        lon:44.99, lat:12.78, t:'conflict', cap:0.4, util:11, note:'Conflict zone. Effectively non-operational since 2015 civil war. Previously a key Red Sea transit terminal.', source:'Lloyd\'s List'},
  {id:'hod', n:'Hodeidah',      c:'Yemen',        lon:42.95, lat:14.80, t:'conflict', cap:0.6, util:8,  note:'Houthi-controlled. Humanitarian access only. Severe damage to infrastructure.', source:'UN OCHA'},
  {id:'dj',  n:'Djibouti',      c:'Djibouti',     lon:43.15, lat:11.60, t:'strategic',cap:0.8, util:62, note:'Bab el-Mandeb gateway state. US, French, Chinese military bases present. Critical access port for Red Sea chokepoint.', source:'Djibouti Port Authority'},
  {id:'sal', n:'Salalah',       c:'Oman',         lon:54.00, lat:16.94, t:'export',   cap:1.0, util:55, note:'South Oman port. Outside Hormuz. Growing strategic value as bypass terminal. Receiving transshipment diverted from Red Sea.', source:'Port of Salalah'},
  {id:'cy',  n:'Ceyhan',        c:'Turkey',       lon:35.90, lat:36.65, t:'export',   cap:1.6, util:58, note:'Terminus of Kirkuk-Ceyhan and BTC pipelines. Currently constrained by KRG-Baghdad dispute reducing northern Iraq throughput.', source:'Botas Turkey'},
  {id:'abk', n:'Ras al-Khair',  c:'Saudi Arabia', lon:49.28, lat:27.43, t:'export',   cap:1.1, util:65, note:'Industrial port supporting SABIC and Ma\'aden industrial complex. Growing petrochemical export role.', source:'Saudi Ports Authority'},
],

/* ── Pipelines ─────────────────────────────────────────────── */
pipelines:[
  {n:'East-West Pipeline',    from:[50.2,26.7], to:[38.1,24.1], cap:'5M bbl/d',   status:'active',    col:'#1F5A94', note:'Abqaiq→Yanbu. Only pipeline bypass of Hormuz at scale — but Yanbu port (1.8M bbl/d) is the binding constraint, not the pipeline itself.'},
  {n:'ADCO / Abu Dhabi Crude',from:[53.5,23.5], to:[56.4,25.1], cap:'1.5M bbl/d', status:'active',    col:'#1F5A94', note:'Habshan→Fujairah. UAE pipeline bypassing Hormuz to east coast terminal. Operational and strategic.'},
  {n:'Kirkuk–Ceyhan',         from:[44.4,35.5], to:[35.9,36.6], cap:'1.6M bbl/d', status:'disrupted', col:'#C58B2A', note:'Iraq→Turkey. Severely underutilised (~12% capacity) due to unresolved KRG-Baghdad political dispute. No timeline for resolution.'},
  {n:'BTC Pipeline',          from:[49.8,40.4], to:[35.9,36.6], cap:'1.2M bbl/d', status:'active',    col:'#1F5A94', note:'Baku–Tbilisi–Ceyhan. Azeri and Kazakh crude to Mediterranean. Operational and stable.'},
  {n:'SUMED Pipeline',        from:[32.3,30.7], to:[29.9,32.6], cap:'2.5M bbl/d', status:'active',    col:'#1F5A94', note:'Egypt. Suez-Mediterranean bypass pipeline. Growing in importance as Suez Canal traffic reduces due to Red Sea crisis.'},
  {n:'IPSA (Iraq-Saudi)',      from:[46.3,30.5], to:[37.0,22.5], cap:'1.65M bbl/d',status:'inactive',  col:'#9AACBD', note:'Closed since 1990 Gulf War. Periodic reopening discussions but no operational timeline. Would provide Iraq Red Sea access if restored.'},
],

/* ── Chokepoints ───────────────────────────────────────────── */
chokepoints:[
  {
    n:'Strait of Hormuz', lon:56.6, lat:26.5,
    risk:'high', riskLabel:'High',
    vol:'21M bbl/d', share:'~20% of global oil supply',
    riskTypes:[
      {type:'Geopolitical', level:'high',  src:'US State Dept Travel Advisory Level 3', updated:'Feb 2026'},
      {type:'Conflict proximity', level:'high', src:'ACLED armed events database', updated:'Mar 2026'},
      {type:'Shipping',   level:'elevated',src:'Lloyd\'s Market Association JWC area', updated:'Jan 2026'},
    ],
    note:'Minimum navigable width ~3.4km. Iran has repeatedly threatened closure. Any sustained restriction would spike Asian crude differentials within 48 hours and affect ~35% of globally traded LNG.'
  },
  {
    n:'Bab el-Mandeb', lon:43.4, lat:12.6,
    risk:'high', riskLabel:'High',
    vol:'9M bbl/d', share:'Red Sea gateway — EU energy exposure',
    riskTypes:[
      {type:'Active conflict', level:'high',  src:'ACLED Yemen conflict tracker', updated:'Mar 2026'},
      {type:'Shipping',        level:'high',  src:'Lloyd\'s Market Association JWC area', updated:'Mar 2026'},
      {type:'Geopolitical',    level:'high',  src:'US State Dept Yemen Level 4: Do Not Travel', updated:'Mar 2026'},
    ],
    note:'Houthi drone and missile operations ongoing. Major shipping lines rerouting via Cape of Good Hope adding ~14 days and ~$1.2M per voyage. EU gas imports via LNG tankers particularly exposed.'
  },
  {
    n:'Suez Canal', lon:32.3, lat:30.7,
    risk:'moderate', riskLabel:'Moderate',
    vol:'2.5M bbl/d', share:'Med gateway',
    riskTypes:[
      {type:'Geopolitical', level:'moderate', src:'US State Dept Egypt Level 2', updated:'Jan 2026'},
      {type:'Shipping',     level:'low',     src:'Standard marine route — no active restriction', updated:'Mar 2026'},
    ],
    note:'Canal itself is operationally normal. Reduced traffic driven by upstream Bab el-Mandeb disruption rerouting tankers via Cape. Canal Authority revenues under pressure.'
  },
],

/* ── Export flows ─────────────────────────────────────────── */
/* from: [lon, lat], to: [lon, lat], vol in M bbl/d */
flows:[
  {from:[50.2,26.7], to:[104,35],  label:'SA → China',    vol:2.1,  exporter:'Saudi Arabia', importer:'China',       route:'Hormuz'},
  {from:[50.2,26.7], to:[78,20],   label:'SA → India',    vol:1.4,  exporter:'Saudi Arabia', importer:'India',       route:'Hormuz'},
  {from:[50.2,26.7], to:[135,36],  label:'SA → Japan',    vol:1.2,  exporter:'Saudi Arabia', importer:'Japan',       route:'Hormuz'},
  {from:[50.2,26.7], to:[127,37],  label:'SA → Korea',    vol:0.9,  exporter:'Saudi Arabia', importer:'South Korea', route:'Hormuz'},
  {from:[48.8,30.0], to:[104,35],  label:'Iraq → China',  vol:1.8,  exporter:'Iraq',         importer:'China',       route:'Hormuz'},
  {from:[48.8,30.0], to:[78,20],   label:'Iraq → India',  vol:0.8,  exporter:'Iraq',         importer:'India',       route:'Hormuz'},
  {from:[48.8,30.0], to:[13,52],   label:'Iraq → Europe', vol:0.6,  exporter:'Iraq',         importer:'Europe',      route:'Suez/Med'},
  {from:[55.0,24.5], to:[135,36],  label:'UAE → Japan',   vol:0.7,  exporter:'UAE',          importer:'Japan',       route:'Hormuz'},
  {from:[55.0,24.5], to:[104,35],  label:'UAE → China',   vol:0.9,  exporter:'UAE',          importer:'China',       route:'Hormuz'},
  {from:[55.4,25.0], to:[49.3,30.6],label:'Russia → ME transit',vol:0.3, exporter:'Russia', importer:'India via Gulf',route:'Indian Ocean'},
  {from:[37.6,55.8], to:[13,52],   label:'Russia → Europe',vol:0.8, exporter:'Russia',       importer:'Europe',      route:'Pipeline + Baltic'},
  {from:[37.6,55.8], to:[104,35],  label:'Russia → China', vol:2.2, exporter:'Russia',       importer:'China',       route:'Eastern Siberia pipeline'},
  {from:[37.6,55.8], to:[78,20],   label:'Russia → India', vol:1.6, exporter:'Russia',       importer:'India',       route:'Cape / Indian Ocean'},
],

/* ── Country data — map hover ─────────────────────────────── */
countries:{
  682:{n:'Saudi Arabia',  osp:'$162.10', risk:'moderate', prod:'10.2M bbl/d', type:'Arab Light / Heavy',    dest:'China, Japan, India', crude:162.1, producer:1, url:'saudi-arabia.html'},
  784:{n:'UAE',           osp:'$163.20', risk:'low',      prod:'3.7M bbl/d',  type:'Murban, Upper Zakum',   dest:'Japan, India, China', crude:163.2, producer:1},
  414:{n:'Kuwait',        osp:'$157.80', risk:'low',      prod:'2.9M bbl/d',  type:'Kuwait Export Crude',   dest:'Japan, Korea, India', crude:157.8, producer:1},
  368:{n:'Iraq',          osp:'$158.20', risk:'elevated', prod:'4.5M bbl/d',  type:'Basra Light / Heavy',   dest:'China, India, US, EU',crude:158.2, producer:1},
  364:{n:'Iran',          osp:'Sanctioned',risk:'high',   prod:'~3.0M bbl/d', type:'Shadow fleet exports',  dest:'China (est.)',         crude:null,  conflict:1},
  887:{n:'Yemen',         osp:'Conflict', risk:'high',    prod:'Negligible',   type:'Houthi-controlled',    dest:'—',                   crude:null,  conflict:1},
  512:{n:'Oman',          osp:'$161.40', risk:'low',      prod:'1.1M bbl/d',  type:'Oman sour crude',       dest:'China, India',        crude:161.4, producer:1},
  634:{n:'Qatar',         osp:'$158.60', risk:'low',      prod:'1.8M bbl/d',  type:'Marine crude + LNG',    dest:'Japan, Korea, UK',    crude:158.6, producer:1},
  48: {n:'Bahrain',       osp:'N/A',     risk:'low',      prod:'0.2M bbl/d',  type:'Bahrain crude (BAPCO)', dest:'Japan, India',        crude:null,  producer:1},
  400:{n:'Jordan',        osp:'Importer',risk:'moderate', prod:'None',          type:'Net importer',         dest:'—',                   crude:null},
  760:{n:'Syria',         osp:'—',       risk:'high',     prod:'Minimal',      type:'Conflict zone',         dest:'—',                   crude:null,  conflict:1},
  376:{n:'Israel',        osp:'—',       risk:'elevated', prod:'Gas only',     type:'Tamar, Leviathan gas',  dest:'Egypt, Jordan',       crude:null},
  422:{n:'Lebanon',       osp:'—',       risk:'elevated', prod:'None',          type:'Exploration stage',    dest:'—',                   crude:null,  conflict:1},
  818:{n:'Egypt',         osp:'—',       risk:'moderate', prod:'Declining',    type:'Transit / Suez revenues',dest:'—',                  crude:null},
  792:{n:'Turkey',        osp:'—',       risk:'moderate', prod:'Minimal',      type:'Transit hub, Ceyhan',   dest:'—',                   crude:null},
  398:{n:'Kazakhstan',    osp:'$138.20', risk:'low',      prod:'1.9M bbl/d',   type:'Tengiz, Kashagan crude',dest:'China, EU via BTC',   crude:138.2, producer:1},
  31: {n:'Azerbaijan',    osp:'$130.40', risk:'moderate', prod:'0.7M bbl/d',   type:'ACG crude via BTC',    dest:'Europe via Ceyhan',   crude:130.4, producer:1},
  795:{n:'Turkmenistan',  osp:'—',       risk:'low',      prod:'0.3M bbl/d',   type:'Gas / Galkynysh',      dest:'China (pipeline)',     crude:null},
  860:{n:'Uzbekistan',    osp:'—',       risk:'low',      prod:'0.06M bbl/d',  type:'Landlocked',            dest:'CIS',                 crude:null},
  762:{n:'Tajikistan',    osp:'—',       risk:'moderate', prod:'None',          type:'Landlocked',            dest:'—',                   crude:null},
  417:{n:'Kyrgyzstan',    osp:'—',       risk:'low',      prod:'None',          type:'Landlocked',            dest:'—',                   crude:null},
  4:  {n:'Afghanistan',   osp:'—',       risk:'high',     prod:'None',          type:'Landlocked, transit',   dest:'—',                   crude:null,  conflict:1},
  586:{n:'Pakistan',      osp:'—',       risk:'moderate', prod:'Minimal',      type:'Major LNG importer',    dest:'—',                   crude:null},
  706:{n:'Somalia',       osp:'—',       risk:'high',     prod:'None',          type:'Piracy corridor',       dest:'—',                   crude:null},
  231:{n:'Ethiopia',      osp:'—',       risk:'elevated', prod:'None',          type:'Landlocked',            dest:'—',                   crude:null},
  788:{n:'Tunisia',       osp:'—',       risk:'moderate', prod:'Minor',        type:'Minor producer',        dest:'—',                   crude:null},
  434:{n:'Libya',         osp:'—',       risk:'high',     prod:'1.2M bbl/d',   type:'Light sweet crude',     dest:'Europe',              crude:null,  producer:1},
  268:{n:'Georgia',       osp:'—',       risk:'moderate', prod:'None',          type:'Transit — BTC pipeline',dest:'—',                  crude:null},
  51: {n:'Armenia',       osp:'—',       risk:'moderate', prod:'None',          type:'Landlocked',            dest:'—',                   crude:null},
  196:{n:'Cyprus',        osp:'—',       risk:'low',      prod:'Exploration',  type:'Aphrodite gas field',   dest:'—',                   crude:null},
  300:{n:'Greece',        osp:'—',       risk:'low',      prod:'Minor',        type:'EU member',             dest:'—',                   crude:null},
  100:{n:'Bulgaria',      osp:'—',       risk:'low',      prod:'None',          type:'EU member',             dest:'—',                   crude:null},
  356:{n:'India',         osp:'—',       risk:'low',      prod:'0.7M bbl/d',   type:'Major importer',        dest:'—',                   crude:null},
  729:{n:'Sudan',         osp:'—',       risk:'high',     prod:'Minimal',      type:'Post-conflict',         dest:'—',                   crude:null,  conflict:1},
  504:{n:'Morocco',       osp:'—',       risk:'low',      prod:'Minor',        type:'Refining hub',          dest:'—',                   crude:null},
  12: {n:'Algeria',       osp:'—',       risk:'moderate', prod:'1.3M bbl/d',   type:'Saharan Blend crude',   dest:'Europe',              crude:null,  producer:1},
  566:{n:'Nigeria',       osp:'—',       risk:'elevated', prod:'1.3M bbl/d',   type:'Bonny Light crude',     dest:'Europe, India',       crude:null,  producer:1},
  642:{n:'Romania',       osp:'—',       risk:'low',      prod:'Modest',       type:'EU member',             dest:'—',                   crude:null},
  643:{n:'Russia',        osp:'$108.50', risk:'high',     prod:'9.2M bbl/d',   type:'Urals, ESPO Blend',     dest:'China, India',        crude:108.5, producer:1, sanctioned:1},
  156:{n:'China',         osp:'$136.80', risk:'low',      prod:'4.3M bbl/d',   type:'Daqing + major importer',dest:'—',                 crude:136.8, producer:1},
  356:{n:'India',         osp:'—',       risk:'low',      prod:'0.8M bbl/d',   type:'Major importer',        dest:'—',                   crude:null},
  792:{n:'Turkey',        osp:'—',       risk:'moderate', prod:'Minimal',      type:'Ceyhan terminal hub',   dest:'—',                   crude:null},
  724:{n:'Spain',         osp:'—',       risk:'low',      prod:'None',          type:'EU importer',           dest:'—',                   crude:null},
  276:{n:'Germany',       osp:'—',       risk:'low',      prod:'None',          type:'EU importer',           dest:'—',                   crude:null},
  380:{n:'Italy',         osp:'—',       risk:'low',      prod:'None',          type:'EU importer',           dest:'—',                   crude:null},
  250:{n:'France',        osp:'—',       risk:'low',      prod:'None',          type:'EU importer',           dest:'—',                   crude:null},
  826:{n:'United Kingdom',osp:'—',       risk:'low',      prod:'0.9M bbl/d',   type:'North Sea producer',    dest:'—',                   crude:null},
  840:{n:'United States', osp:'$134.20', risk:'low',      prod:'13.3M bbl/d',  type:'WTI — world\'s largest producer',dest:'—',         crude:134.2, producer:1},
  124:{n:'Canada',        osp:'—',       risk:'low',      prod:'5.6M bbl/d',   type:'Oil sands + conventional',dest:'US',              crude:null,  producer:1},
  484:{n:'Mexico',        osp:'—',       risk:'moderate', prod:'1.8M bbl/d',   type:'Maya heavy crude',      dest:'US, Asia',            crude:null,  producer:1},
  682:{n:'Saudi Arabia',  osp:'$162.10', risk:'moderate', prod:'10.2M bbl/d',  type:'Arab Light / Heavy',    dest:'China, Japan, India', crude:162.1, producer:1, url:'saudi-arabia.html'},
},

/* ── Saudi Arabia country page data ────────────────────────── */
saudiArabia:{
  name:'Saudi Arabia',
  capital:'Riyadh',
  region:'Arabian Peninsula',
  production:'10.2M bbl/d',
  reserves:'267 billion barrels (17% of global)',
  opecQuota:'10.0M bbl/d',
  mainGrades:['Arab Light (33° API)', 'Arab Medium (31° API)', 'Arab Heavy (27° API)', 'Arab Extra Light (37° API)'],
  nationalCo:'Saudi Aramco (Saudi Arabian Oil Co.)',
  govtRevOil:'~70% of government revenues',
  nodesOfInterest:[
    {n:'Abqaiq',     lon:49.67,lat:26.0,  type:'processing', note:'World\'s largest oil processing facility. Handles ~7% of global supply. September 2019 drone attack demonstrated extreme strategic vulnerability.'},
    {n:'Ghawar',     lon:49.3, lat:25.5,  type:'field',      note:'Largest conventional oil field in the world. Estimated 3.8M bbl/d production capacity. Declining naturally but still dominant.'},
    {n:'Haradh',     lon:49.2, lat:24.15, type:'field',      note:'Southern Ghawar extension. Gas injection maintains reservoir pressure. Key to sustaining Saudi output levels.'},
    {n:'Khurais',    lon:48.3, lat:25.1,  type:'field',      note:'Second largest Saudi field. Capacity ~1.5M bbl/d. Master Gas System connected.'},
    {n:'Jubail',     lon:49.66,lat:27.0,  type:'industrial', note:'Industrial city and export terminal. Refining and petrochemical complex.'},
    {n:'Ras Tanura', lon:50.17,lat:26.65, type:'port',       note:'World\'s largest crude export terminal. East coast — entirely dependent on Hormuz access.'},
    {n:'Yanbu',      lon:38.05,lat:24.08, type:'port',       note:'Red Sea terminal. Receives East-West pipeline. Port capacity 1.8M bbl/d — the binding Hormuz bypass constraint.'},
  ],
  priceHistory:[
    {month:'Oct 25', brent:118, arabLight:136, arabHeavy:129},
    {month:'Nov 25', brent:122, arabLight:140, arabHeavy:133},
    {month:'Dec 25', brent:126, arabLight:145, arabHeavy:137},
    {month:'Jan 26', brent:130, arabLight:150, arabHeavy:142},
    {month:'Feb 26', brent:135, arabLight:157, arabHeavy:149},
    {month:'Mar 26', brent:138, arabLight:162, arabHeavy:155},
  ],
  topBuyers:[
    {country:'China',      share:23, vol:'2.1M bbl/d', flag:'🇨🇳'},
    {country:'Japan',      share:14, vol:'1.2M bbl/d', flag:'🇯🇵'},
    {country:'India',      share:13, vol:'1.1M bbl/d', flag:'🇮🇳'},
    {country:'South Korea',share:11, vol:'0.9M bbl/d', flag:'🇰🇷'},
    {country:'United States',share:8, vol:'0.7M bbl/d',flag:'🇺🇸'},
    {country:'Other',      share:31, vol:'2.8M bbl/d', flag:'🌐'},
  ],
  risks:[
    {type:'Shipping / Hormuz',   level:'elevated', detail:'~95% of exports transit Hormuz. East-West pipeline capacity constrained by Yanbu port (1.8M bbl/d vs 5M bbl/d pipeline).', src:'IEA, Aramco annual report', updated:'Mar 2026'},
    {type:'Geopolitical',        level:'moderate', detail:'State Dept Level 2 advisory. Regional tensions elevated. Abqaiq vulnerability demonstrated in 2019.', src:'US State Dept, OSAC', updated:'Feb 2026'},
    {type:'Infrastructure',      level:'elevated', detail:'Yanbu bottleneck limits Red Sea bypass. Single processing hub (Abqaiq) handles majority of oil prep.', src:'IEA World Energy Outlook', updated:'2025'},
    {type:'Sanctions',           level:'low',      detail:'No current sanctions. Strong US-Saudi relationship. Subject to change with geopolitical shifts.', src:'OFAC sanctions list', updated:'Mar 2026'},
  ],
  analystNote:{
    title:'The Yanbu bottleneck: why the Red Sea bypass argument fails at scale',
    body:`Saudi Arabia's East-West Pipeline (Petroline) runs 1,200km from Abqaiq in the Eastern Province to Yanbu on the Red Sea, and is routinely cited as the strategic answer to Strait of Hormuz vulnerability. The argument is simple: if Hormuz is disrupted, Saudi Arabia simply diverts exports westward through the pipeline to Yanbu and out through the Red Sea.

This argument has a structural flaw that is rarely made explicit: the pipeline can carry up to 5 million barrels per day. Yanbu's export terminal capacity is approximately 1.8 million barrels per day.

The pipeline is not the bottleneck. The port is.

At current capacity, even fully utilising the East-West Pipeline would allow Saudi Arabia to bypass Hormuz for roughly 18% of its typical daily exports — not 100%. The remaining ~8.4 million barrels per day remain Hormuz-dependent.

The second structural problem is Bab el-Mandeb. The pipeline bypass trades one chokepoint for another. Saudi crude routed via Yanbu must still pass through the Bab el-Mandeb strait — currently rated as the highest-risk maritime chokepoint in the world, with Houthi drone and missile operations ongoing. The Red Sea bypass is not a bypass at all. It is a route that exchanges Hormuz exposure for Bab el-Mandeb exposure, at lower capacity, through a port that is already operating below full utilisation due to infrastructure limits rather than demand.

The only genuine bypass would require significant investment in Yanbu's export infrastructure, which would take years to build and has not been announced.`,
    sources:'IEA World Energy Outlook 2025, Saudi Aramco Annual Review, Platts Gulf shipping data, Lloyd\'s List chokepoint analysis',
    updated:'March 2026'
  }
}

}; /* end window.CONTANGO */
