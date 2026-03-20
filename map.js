/* Contango v3.0 · 20 March 2026 · github.com/pacho064/Contango
/* ================================================================
   CONTANGO — Map Engine
   Full world D3 map with zoom/pan, proper fills, no omissions
   ================================================================ */

window.MapEngine = (function(){

const D = window.CONTANGO;

/* ── State ────────────────────────────────────────────────── */
let svg, g, projection, pathGen, zoom, world;
let activeLayer = 'base';
let sideOpen = false;

/* ── Initial view: Greater Middle East ───────────────────── */
const DEFAULT_CENTER = [48, 25];
const DEFAULT_SCALE  = 680;

/* ── Country fill logic ───────────────────────────────────── */
function isDark(){ return document.documentElement.getAttribute('data-theme') === 'dark'; }

function getCountryFill(id){
  const c = D.countries[+id];
  const dk = isDark();

  if(activeLayer === 'base'){
    if(!c) return dk ? '#1A2230' : '#E8ECF0';
    if(c.conflict) return dk ? '#2C1E1E' : '#E8D8D4';
    if(c.producer) return dk ? '#2A2416' : '#EDE0C4';
    if(c.sanctioned) return dk ? '#221A22' : '#E4D8E4';
    return dk ? '#1A2230' : '#E8ECF0';
  }

  if(activeLayer === 'risk'){
    if(!c) return dk ? '#1A2230' : '#EEF1F4';
    const r = c.risk;
    if(r === 'high')     return dk ? 'rgba(184,80,66,.45)' : 'rgba(184,80,66,.22)';
    if(r === 'elevated') return dk ? 'rgba(192,112,32,.42)' : 'rgba(192,112,32,.2)';
    if(r === 'moderate') return dk ? 'rgba(184,134,11,.38)' : 'rgba(184,134,11,.15)';
    return dk ? 'rgba(46,125,90,.3)' : 'rgba(46,125,90,.12)';
  }

  if(!c) return dk ? '#1A2230' : '#E8ECF0';
  if(c.producer) return dk ? '#2A2416' : '#EDE0C4';
  return dk ? '#1A2230' : '#E8ECF0';
}

function getBorderColor(){
  return isDark() ? '#2A3444' : '#C2CDD8';
}
function getBorderWidth(id){
  const c = D.countries[+id];
  if(c && (c.producer || c.conflict)) return 0.7;
  return 0.4;
}

/* ── Sea label definitions ────────────────────────────────── */
const SEA_LABELS = [
  {t:'Persian Gulf',   lon:51.0, lat:27.0, sz:9},
  {t:'Arabian Sea',    lon:63.0, lat:18.0, sz:10},
  {t:'Red Sea',        lon:38.0, lat:21.5, sz:8.5, rot:-55},
  {t:'Gulf of Aden',   lon:47.0, lat:11.5, sz:8},
  {t:'Caspian Sea',    lon:51.5, lat:42.5, sz:8},
  {t:'Mediterranean',  lon:20.0, lat:35.0, sz:9},
  {t:'Indian Ocean',   lon:72.0, lat:10.0, sz:11},
  {t:'Black Sea',      lon:33.0, lat:43.0, sz:8},
  {t:'Atlantic Ocean', lon:-25.0,lat:30.0, sz:11},
  {t:'Pacific Ocean',  lon:160.0,lat:15.0, sz:11},
  {t:'Arctic Ocean',   lon:0,    lat:82.0, sz:10},
  {t:'South China Sea',lon:113.0,lat:14.0, sz:8.5},
  {t:'Bay of Bengal',  lon:88.0, lat:14.0, sz:8.5},
  {t:'Persian Gulf',   lon:51.0, lat:27.0, sz:9},
];

/* ── City markers ─────────────────────────────────────────── */
const CITIES = [
  {n:'Riyadh',      lon:46.72,lat:24.69, sz:'lg'},
  {n:'Tehran',      lon:51.42,lat:35.69, sz:'lg'},
  {n:'Baghdad',     lon:44.44,lat:33.34, sz:'lg'},
  {n:'Cairo',       lon:31.25,lat:30.06, sz:'lg'},
  {n:'Ankara',      lon:32.86,lat:39.93, sz:'md'},
  {n:'Abu Dhabi',   lon:54.37,lat:24.47, sz:'md'},
  {n:'Muscat',      lon:58.59,lat:23.61, sz:'md'},
  {n:"Kuwait City", lon:47.98,lat:29.37, sz:'md'},
  {n:"Sana'a",      lon:44.21,lat:15.37, sz:'sm'},
  {n:'Doha',        lon:51.53,lat:25.29, sz:'sm'},
  {n:'Amman',       lon:35.94,lat:31.96, sz:'sm'},
  {n:'Astana',      lon:71.43,lat:51.18, sz:'sm'},
  {n:'Baku',        lon:49.87,lat:40.41, sz:'sm'},
  {n:'Islamabad',   lon:73.07,lat:33.72, sz:'sm'},
  {n:'Moscow',      lon:37.62,lat:55.75, sz:'md'},
  {n:'Delhi',       lon:77.21,lat:28.63, sz:'md'},
  {n:'Beijing',     lon:116.4,lat:39.91, sz:'md'},
];

/* ── Country labels ───────────────────────────────────────── */
const CTRY_LBLS = [
  {lon:44.5, lat:23.5,  t:'Saudi Arabia',   sz:10, w:600},
  {lon:53.5, lat:32.5,  t:'Iran',           sz:10, w:600},
  {lon:43.8, lat:33.2,  t:'Iraq',           sz:9,  w:500},
  {lon:67.5, lat:48.5,  t:'Kazakhstan',     sz:9,  w:500},
  {lon:29.5, lat:26.0,  t:'Egypt',          sz:9,  w:500},
  {lon:33.5, lat:39.2,  t:'Turkey',         sz:9,  w:500},
  {lon:69.0, lat:30.0,  t:'Pakistan',       sz:8.5,w:500},
  {lon:57.5, lat:22.0,  t:'Oman',           sz:8,  w:400},
  {lon:54.5, lat:23.8,  t:'UAE',            sz:7.5,w:400},
  {lon:47.5, lat:15.5,  t:'Yemen',          sz:8,  w:400},
  {lon:65.0, lat:34.0,  t:'Afghanistan',    sz:8,  w:400},
  {lon:64.5, lat:41.5,  t:'Uzbekistan',     sz:7.5,w:400},
  {lon:58.5, lat:38.5,  t:'Turkmenistan',   sz:7.5,w:400},
  {lon:47.5, lat:40.5,  t:'Azerbaijan',     sz:7,  w:400},
  {lon:17.5, lat:27.0,  t:'Libya',          sz:8,  w:400},
  {lon:38.5, lat:35.0,  t:'Syria',          sz:7.5,w:400},
  {lon:51.5, lat:25.4,  t:'Qatar',          sz:7,  w:400},
  {lon:47.5, lat:29.3,  t:'Kuwait',         sz:7,  w:400},
  {lon:35.2, lat:31.5,  t:'Israel',         sz:6.5,w:400},
  {lon:35.5, lat:34.0,  t:'Lebanon',        sz:6,  w:400},
  {lon:27.0, lat:16.0,  t:'Sudan',          sz:8,  w:400},
  {lon:40.5, lat:9.0,   t:'Ethiopia',       sz:8,  w:400},
  {lon:17.0, lat:15.5,  t:'Chad',           sz:7.5,w:400},
  {lon:8.0,  lat:17.0,  t:'Niger',          sz:7.5,w:400},
  {lon:44.0, lat:6.0,   t:'Somalia',        sz:7.5,w:400},
  {lon:37.9, lat:55.75, t:'Russia',         sz:10, w:600},
  {lon:104,  lat:35,    t:'China',          sz:11, w:600},
  {lon:78,   lat:22,    t:'India',          sz:10, w:600},
  {lon:35.0, lat:26.5,  t:'Jordan',         sz:7,  w:400},
  {lon:9.0,  lat:34.0,  t:'Tunisia',        sz:7,  w:400},
  {lon:2.0,  lat:28.5,  t:'Algeria',        sz:8.5,w:500},
  {lon:8.0,  lat:9.0,   t:'Nigeria',        sz:8,  w:500},
  {lon:-97,  lat:38,    t:'United States',  sz:11, w:600},
  {lon:-60,  lat:-15,   t:'Brazil',         sz:10, w:500},
];

/* ── Build ─────────────────────────────────────────────────── */
function build(containerId, opts){
  opts = opts || {};
  const container = document.getElementById(containerId);
  if(!container) return;

  const W = container.offsetWidth || 960;
  const H = opts.height || 520;

  svg = d3.select('#' + containerId);
  svg.attr('viewBox', `0 0 ${W} ${H}`);

  /* Projection — Mercator, default Greater Middle East view */
  projection = d3.geoMercator()
    .center(DEFAULT_CENTER)
    .scale(DEFAULT_SCALE)
    .translate([W/2, H/2]);

  pathGen = d3.geoPath().projection(projection);

  /* Zoom behaviour */
  zoom = d3.zoom()
    .scaleExtent([0.3, 40])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
      /* scale labels/symbols inversely so they stay readable */
      const k = event.transform.k;
      g.selectAll('.city-dot').attr('r', Math.max(1.5, 3.5/Math.sqrt(k)));
      g.selectAll('.port-dot').attr('r', d => Math.max(2, portRadius(d)/Math.sqrt(k)));
      g.selectAll('.chokepoint-ring').attr('r', d => Math.max(5, 10/Math.sqrt(k)));
      g.selectAll('.clbl').style('font-size', d => Math.max(7, (d.sz||8)/Math.sqrt(k))+'px');
    });

  svg.call(zoom);

  /* Background group */
  svg.append('rect').attr('class','sea-bg')
    .attr('width',W).attr('height',H)
    .attr('fill', isDark() ? '#131C28' : '#D8EAF5');

  /* All map content in one scalable group */
  g = svg.append('g').attr('class','map-g');

  /* Load world topology */
  d3.json('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json').then(topo => {
    world = topo;
    drawLand();
    drawLabels();
    drawCities();
    drawOverlays();
    if(opts.onReady) opts.onReady();
  }).catch(err => {
    svg.append('text').attr('x',W/2).attr('y',H/2)
      .attr('text-anchor','middle').attr('fill','#888').attr('font-size',14)
      .attr('font-family','IBM Plex Sans,sans-serif')
      .text('Map requires internet connection — please reload');
  });
}

/* ── Draw all land — EVERY country ───────────────────────── */
function drawLand(){
  const features = topojson.feature(world, world.objects.countries).features;

  g.selectAll('.ctry').data(features).join('path')
    .attr('class','ctry')
    .attr('d', pathGen)
    .attr('fill', d => getCountryFill(+d.id))
    .attr('stroke', getBorderColor())
    .attr('stroke-width', d => getBorderWidth(+d.id))
    .style('cursor','pointer')
    .on('mouseover', function(event, d){ onCountryHover(event, +d.id); })
    .on('mouseleave', onCountryLeave)
    .on('click', function(event, d){ onCountryClick(event, +d.id); });

  /* Sea labels */
  SEA_LABELS.forEach(sl => {
    const [sx,sy] = projection([sl.lon, sl.lat]);
    const rot = sl.rot ? `rotate(${sl.rot},${sx},${sy})` : null;
    g.append('text').attr('class','sea-lbl')
      .attr('x',sx).attr('y',sy)
      .attr('text-anchor','middle')
      .attr('dominant-baseline','middle')
      .attr('font-size', sl.sz)
      .attr('font-style','italic')
      .attr('font-family','Source Serif 4,serif')
      .attr('fill', isDark() ? 'rgba(140,180,220,.5)' : 'rgba(30,70,110,.32)')
      .attr('pointer-events','none')
      .attr('letter-spacing','.04em')
      .attr('transform', rot)
      .text(sl.t);
  });
}

/* ── Country labels ───────────────────────────────────────── */
function drawLabels(){
  CTRY_LBLS.forEach(lb => {
    const [lx,ly] = projection([lb.lon, lb.lat]);
    /* halo pass */
    g.append('text').attr('class','clbl clbl-halo')
      .attr('x',lx).attr('y',ly)
      .attr('text-anchor','middle').attr('dominant-baseline','middle')
      .attr('font-size', lb.sz).attr('font-weight', lb.w)
      .attr('font-family','IBM Plex Sans,sans-serif')
      .attr('letter-spacing','.07em')
      .attr('pointer-events','none')
      .attr('fill', isDark() ? '#131C28' : '#ffffff')
      .attr('stroke', isDark() ? '#131C28' : '#ffffff')
      .attr('stroke-width', 3).attr('paint-order','stroke')
      .datum({sz:lb.sz})
      .text(lb.t.toUpperCase());
    /* label pass */
    g.append('text').attr('class','clbl clbl-text')
      .attr('x',lx).attr('y',ly)
      .attr('text-anchor','middle').attr('dominant-baseline','middle')
      .attr('font-size', lb.sz).attr('font-weight', lb.w)
      .attr('font-family','IBM Plex Sans,sans-serif')
      .attr('letter-spacing','.07em')
      .attr('pointer-events','none')
      .attr('fill', isDark() ? 'rgba(220,210,195,.6)' : 'rgba(20,28,40,.48)')
      .datum({sz:lb.sz})
      .text(lb.t.toUpperCase());
  });
}

/* ── City dots ────────────────────────────────────────────── */
function drawCities(){
  CITIES.forEach(city => {
    const [cx,cy] = projection([city.lon, city.lat]);
    const r = city.sz==='lg'?3.5:city.sz==='md'?2.5:1.8;
    const cg = g.append('g').attr('class','city-g').attr('pointer-events','none');
    /* halo */
    cg.append('circle').attr('cx',cx).attr('cy',cy).attr('r',r+2.5)
      .attr('class','city-halo')
      .attr('fill', isDark() ? 'rgba(19,28,40,.6)' : 'rgba(255,255,255,.55)')
      .attr('stroke','none');
    /* dot */
    cg.append('circle').attr('cx',cx).attr('cy',cy).attr('r',r)
      .attr('class','city-dot')
      .attr('fill', isDark() ? '#C8C0B0' : '#1B2430')
      .attr('stroke', isDark() ? '#131C28' : '#f7f8fa')
      .attr('stroke-width',1);
    /* name */
    const offX = cx > 800 ? -r-4 : r+4;
    const anchor = cx > 800 ? 'end' : 'start';
    const nsz = city.sz==='lg'?8:7.5;
    cg.append('text').attr('x',cx+offX).attr('y',cy+1)
      .attr('text-anchor',anchor).attr('dominant-baseline','middle')
      .attr('font-size',nsz).attr('font-family','IBM Plex Sans,sans-serif')
      .attr('fill', isDark() ? '#131C28' : '#ffffff')
      .attr('stroke', isDark() ? '#131C28' : '#ffffff')
      .attr('stroke-width',2.5).attr('paint-order','stroke')
      .attr('pointer-events','none').text(city.n);
    cg.append('text').attr('x',cx+offX).attr('y',cy+1)
      .attr('text-anchor',anchor).attr('dominant-baseline','middle')
      .attr('font-size',nsz).attr('font-family','IBM Plex Sans,sans-serif')
      .attr('fill', isDark() ? 'rgba(200,192,176,.7)' : 'rgba(20,28,40,.62)')
      .attr('pointer-events','none').text(city.n);
  });
}

/* ── Port radius helper ───────────────────────────────────── */
function portRadius(p){ return p.t==='conflict'?4:Math.max(3.5,Math.sqrt(p.cap)*2.3); }

/* ── Overlays ─────────────────────────────────────────────── */
function drawOverlays(){
  g.selectAll('.ov').remove();

  /* ── Ports ──────────────────────────────────────────────── */
  D.ports.forEach(p => {
    const [px,py] = projection([p.lon, p.lat]);
    const col = p.t==='conflict'?'#B85042':p.t==='strategic'?'#6B7C93':'#1F5A94';
    const r = portRadius(p);
    const og = g.append('g').attr('class','ov port-g').style('cursor','pointer').datum(p);

    og.append('circle').attr('cx',px).attr('cy',py).attr('r',r+2)
      .attr('fill','none')
      .attr('stroke', isDark()?'rgba(0,0,0,.35)':'rgba(0,0,0,.1)')
      .attr('stroke-width',2);
    og.append('circle').attr('cx',px).attr('cy',py).attr('r',r)
      .attr('class','port-dot').attr('fill',col).attr('opacity',.9)
      .attr('stroke', isDark()?'#11161C':'#f7f8fa').attr('stroke-width',1.2)
      .datum(p);

    /* near-capacity ring */
    if(p.util > 88){
      og.append('circle').attr('cx',px).attr('cy',py).attr('r',r+6)
        .attr('fill','none').attr('stroke','#B85042')
        .attr('stroke-width',1).attr('opacity',.4)
        .attr('stroke-dasharray','3 2');
    }

    og.on('mousemove', ev => showTT(ev,
      `<div class="map-tt-name">${p.n}</div>
       <div class="map-tt-row"><span class="map-tt-l">Country</span><span class="map-tt-v">${p.c}</span></div>
       <div class="map-tt-row"><span class="map-tt-l">Capacity</span><span class="map-tt-v">${p.cap}M bbl/d</span></div>
       <div class="map-tt-row"><span class="map-tt-l">Utilisation</span><span class="map-tt-v" style="color:${p.util>88?'#B85042':p.util>72?'#C58B2A':'#2E7D5A'}">${p.util}%</span></div>
       <div style="font-size:10px;opacity:.5;margin-top:6px;font-style:italic">${p.note}</div>`))
    .on('mouseleave', hideTT)
    .on('click', () => openPortPanel(p));
  });

  /* ── Chokepoints ─────────────────────────────────────────── */
  D.chokepoints.forEach(cp => {
    const [cx,cy] = projection([cp.lon, cp.lat]);
    const col = cp.risk==='high'?'#B85042':cp.risk==='elevated'?'#C58B2A':'#C58B2A';
    const cg = g.append('g').attr('class','ov chokepoint-g').style('cursor','pointer');
    cg.append('circle').attr('cx',cx).attr('cy',cy).attr('r',12)
      .attr('class','chokepoint-ring')
      .attr('fill','none').attr('stroke',col).attr('stroke-width',.8).attr('opacity',.3);
    cg.append('circle').attr('cx',cx).attr('cy',cy).attr('r',8)
      .attr('fill','none').attr('stroke',col).attr('stroke-width',1.4).attr('opacity',.6);
    cg.append('circle').attr('cx',cx).attr('cy',cy).attr('r',3.5)
      .attr('fill',col).attr('opacity',1);
    cg.on('mousemove', ev => showTT(ev,
      `<div class="map-tt-name">${cp.n}</div>
       <div class="map-tt-row"><span class="map-tt-l">Daily volume</span><span class="map-tt-v">${cp.vol}</span></div>
       <div class="map-tt-row"><span class="map-tt-l">Share</span><span class="map-tt-v">${cp.share}</span></div>
       <div class="map-tt-row"><span class="map-tt-l">Risk level</span><span class="map-tt-v" style="color:${col}">${cp.riskLabel}</span></div>
       <div style="font-size:10px;opacity:.5;margin-top:6px;font-style:italic">${cp.note}</div>`))
    .on('mouseleave', hideTT)
    .on('click', () => openChokePanel(cp));
  });

  /* ── Export flows ─────────────────────────────────────────── */
  drawFlows();
}

/* ── Export flows ─────────────────────────────────────────── */
function drawFlows(){
  g.selectAll('.flow-arc').remove();
  if(activeLayer !== 'flows' && activeLayer !== 'base') return;

  D.flows.forEach(f => {
    const [sx,sy] = projection(f.from);
    const [dx,dy] = projection(f.to);

    /* skip if either end is wildly off screen in base view */
    const bound = 6000;
    if(Math.abs(dx)>bound||Math.abs(dy)>bound) return;

    /* Control point — arc upward */
    const mx = (sx+dx)/2;
    const my = Math.min(sy,dy) - Math.abs(dx-sx)*0.25 - 40;
    const w  = Math.max(1.5, f.vol * 1.4);
    const col = '#C58B2A';

    /* Draw arc */
    g.append('path').attr('class','flow-arc ov')
      .attr('d',`M${sx},${sy} Q${mx},${my} ${dx},${dy}`)
      .attr('fill','none')
      .attr('stroke',col)
      .attr('stroke-width',w)
      .attr('opacity', activeLayer==='flows' ? 0.55 : 0.28)
      .attr('stroke-dasharray', activeLayer==='flows' ? 'none' : '6 4')
      .attr('pointer-events','none');

    /* Arrow head at destination */
    if(activeLayer === 'flows'){
      g.append('circle').attr('class','flow-arc ov')
        .attr('cx',dx).attr('cy',dy).attr('r',w*0.8)
        .attr('fill',col).attr('opacity',.7)
        .attr('pointer-events','none');
      /* destination label */
      g.append('text').attr('class','flow-arc ov')
        .attr('x',dx+(dx>sx?8:-8)).attr('y',dy+3)
        .attr('text-anchor',dx>sx?'start':'end')
        .attr('font-size',8.5)
        .attr('font-family','IBM Plex Sans,sans-serif')
        .attr('font-style','italic')
        .attr('fill', isDark()?'#C58B2A':'#8B5E1A')
        .attr('pointer-events','none')
        .text(f.label);
    }
  });
}

/* ── Layer switching ──────────────────────────────────────── */
function setLayer(name){
  activeLayer = name;
  if(!world) return;
  g.selectAll('.ctry')
    .attr('fill', d => getCountryFill(+d.id))
    .attr('stroke', getBorderColor());
  drawFlows();
}

/* ── Zoom controls ────────────────────────────────────────── */
function zoomIn(){ svg.transition().duration(350).call(zoom.scaleBy,1.6); }
function zoomOut(){ svg.transition().duration(350).call(zoom.scaleBy,0.625); }
function resetView(){
  const W = parseInt(svg.attr('viewBox').split(' ')[2]);
  const H = parseInt(svg.attr('viewBox').split(' ')[3]);
  const t = d3.zoomIdentity.translate(
    W/2 - DEFAULT_SCALE * DEFAULT_CENTER[0] * Math.PI/180,
    H/2
  );
  svg.transition().duration(600).call(zoom.transform, d3.zoomIdentity);
}

/* ── Tooltip ─────────────────────────────────────────────── */
function showTT(ev, html){
  const tt = document.getElementById('map-tt');
  if(!tt) return;
  tt.innerHTML = html; tt.style.opacity = 1;
  const x = ev.clientX+14, y = ev.clientY-18;
  tt.style.left = (x+260>window.innerWidth ? ev.clientX-270 : x)+'px';
  tt.style.top  = Math.max(8,y)+'px';
}
function hideTT(){ const tt=document.getElementById('map-tt'); if(tt) tt.style.opacity=0; }

/* ── Country hover/click ─────────────────────────────────── */
function onCountryHover(ev, id){
  const c = D.countries[id];
  if(!c) return;
  const brent = window._brentPrice || 138.4;
  const prem  = c.crude ? `+$${(c.crude-brent).toFixed(2)} vs Brent` : null;
  const riskColor = {high:'#B85042',elevated:'#C58B2A',moderate:'#B8860B',low:'#2E7D5A'}[c.risk]||'#6B7C93';
  showTT(ev,
    `<div class="map-tt-name">${c.n}${c.url?` <span style="font-size:10px;opacity:.5">→ Country page</span>`:''}</div>
     <div class="map-tt-row"><span class="map-tt-l">Local OSP</span><span class="map-tt-v">${c.osp}${prem?`<br><span style="font-size:10px;color:#C58B2A">${prem}</span>`:''}</span></div>
     <div class="map-tt-row"><span class="map-tt-l">Production</span><span class="map-tt-v">${c.prod}</span></div>
     <div class="map-tt-row"><span class="map-tt-l">Grade</span><span class="map-tt-v">${c.type}</span></div>
     <div class="map-tt-row"><span class="map-tt-l">Risk level</span><span class="map-tt-v" style="color:${riskColor}">${c.risk.charAt(0).toUpperCase()+c.risk.slice(1)}</span></div>`);
}
function onCountryLeave(){ hideTT(); }
function onCountryClick(ev, id){
  const c = D.countries[id];
  if(!c) return;
  if(c.url){ window.location.href = c.url; return; }
  openCountryPanel(id);
}

/* ── Side panels ─────────────────────────────────────────── */
function openCountryPanel(id){
  const c = D.countries[id];
  if(!c) return;
  const panel = document.getElementById('map-side');
  if(!panel) return;
  const brent = window._brentPrice || 138.4;
  const prem  = c.crude ? `+$${(c.crude-brent).toFixed(2)}` : '—';
  const riskCls = {high:'risk-high',elevated:'risk-elev',moderate:'risk-mod',low:'risk-low'}[c.risk]||'risk-low';
  panel.querySelector('.map-side-title').textContent = c.n;
  panel.querySelector('.map-side-body').innerHTML = `
    <div class="msp-row"><span class="msp-label">Local OSP</span><span class="msp-value">${c.osp}</span></div>
    <div class="msp-row"><span class="msp-label">vs Brent today</span><span class="msp-value" style="color:var(--a-amber)">${prem}</span></div>
    <div class="msp-row"><span class="msp-label">Production</span><span class="msp-value">${c.prod}</span></div>
    <div class="msp-row"><span class="msp-label">Crude grade</span><span class="msp-value">${c.type}</span></div>
    <div class="msp-row"><span class="msp-label">Main buyers</span><span class="msp-value">${c.dest}</span></div>
    <div class="msp-row"><span class="msp-label">Risk level</span><span class="msp-value"><span class="risk-badge ${riskCls}">${c.risk}</span></span></div>
    ${c.url?`<div style="margin-top:16px"><a href="${c.url}" style="font-size:13px;color:var(--a-blue);font-family:var(--f-mono)">→ Full country intelligence page</a></div>`:''}
  `;
  openPanel(panel);
}
function openPortPanel(p){
  const panel = document.getElementById('map-side');
  if(!panel) return;
  const col = p.util>88?'var(--a-red)':p.util>72?'var(--a-amber)':'var(--a-green)';
  const riskLabel = p.util>88?'Near capacity':p.util>72?'Elevated':'Normal';
  panel.querySelector('.map-side-title').textContent = p.n;
  panel.querySelector('.map-side-body').innerHTML = `
    <div class="msp-row"><span class="msp-label">Country</span><span class="msp-value">${p.c}</span></div>
    <div class="msp-row"><span class="msp-label">Type</span><span class="msp-value">${p.t.charAt(0).toUpperCase()+p.t.slice(1)} terminal</span></div>
    <div class="msp-row"><span class="msp-label">Capacity</span><span class="msp-value">${p.cap}M bbl/d</span></div>
    <div class="msp-row"><span class="msp-label">Utilisation</span><span class="msp-value" style="color:${col}">${p.util}% — ${riskLabel}</span></div>
    <div style="margin-top:12px;padding:10px;background:var(--bg-subtle);border-radius:5px;font-size:12px;color:var(--t-secondary);line-height:1.55">${p.note}</div>
    <div class="source-line"><div class="source-dot"></div>Source: ${p.source}</div>
  `;
  openPanel(panel);
}
function openChokePanel(cp){
  const panel = document.getElementById('map-side');
  if(!panel) return;
  panel.querySelector('.map-side-title').textContent = cp.n;
  const riskHtml = cp.riskTypes.map(r=>`
    <div class="msp-row">
      <span class="msp-label">${r.type}</span>
      <span class="msp-value"><span class="risk-badge risk-${r.level==='high'?'high':r.level==='elevated'?'elev':r.level==='moderate'?'mod':'low'}">${r.level}</span></span>
    </div>
    <div style="font-size:10px;color:var(--t-meta);font-family:var(--f-mono);padding:0 0 6px">Source: ${r.src} · ${r.updated}</div>
  `).join('');
  panel.querySelector('.map-side-body').innerHTML = `
    <div class="msp-row"><span class="msp-label">Daily volume</span><span class="msp-value">${cp.vol}</span></div>
    <div class="msp-row"><span class="msp-label">Global share</span><span class="msp-value">${cp.share}</span></div>
    <div style="margin-top:4px;margin-bottom:8px;font-size:11px;font-family:var(--f-mono);color:var(--t-meta);text-transform:uppercase;letter-spacing:.07em">Risk components</div>
    ${riskHtml}
    <div style="margin-top:12px;padding:10px;background:var(--bg-subtle);border-radius:5px;font-size:12px;color:var(--t-secondary);line-height:1.55">${cp.note}</div>
  `;
  openPanel(panel);
}
function openPanel(panel){
  panel.classList.add('open');
  sideOpen = true;
}
function closePanel(){
  const panel = document.getElementById('map-side');
  if(panel){ panel.classList.remove('open'); }
  sideOpen = false;
}

/* ── Theme update ─────────────────────────────────────────── */
function updateTheme(){
  if(!world) return;
  svg.select('.sea-bg').attr('fill', isDark() ? '#131C28' : '#D8EAF5');
  g.selectAll('.ctry')
    .attr('fill', d => getCountryFill(+d.id))
    .attr('stroke', getBorderColor());
  g.selectAll('.sea-lbl')
    .attr('fill', isDark() ? 'rgba(140,180,220,.5)' : 'rgba(30,70,110,.32)');
  g.selectAll('.clbl-halo')
    .attr('fill', isDark() ? '#131C28' : '#ffffff')
    .attr('stroke', isDark() ? '#131C28' : '#ffffff');
  g.selectAll('.clbl-text')
    .attr('fill', isDark() ? 'rgba(220,210,195,.6)' : 'rgba(20,28,40,.48)');
  g.selectAll('.city-dot')
    .attr('fill', isDark() ? '#C8C0B0' : '#1B2430')
    .attr('stroke', isDark() ? '#131C28' : '#f7f8fa');
  g.selectAll('.city-halo')
    .attr('fill', isDark() ? 'rgba(19,28,40,.6)' : 'rgba(255,255,255,.55)');
}

/* ── Scale bar ────────────────────────────────────────────── */
function drawScaleBar(){
  const W = parseInt(svg.attr('viewBox').split(' ')[2]);
  const H = parseInt(svg.attr('viewBox').split(' ')[3]);
  svg.selectAll('.scalebar').remove();
  const [p1x] = projection([45,20]);
  const [p2x] = projection([51,20]);
  const bw = Math.round(p2x-p1x);
  const bx = W-bw-20, by = H-18;
  const sc = isDark() ? 'rgba(200,192,176,.45)' : 'rgba(20,28,40,.38)';
  const sb = svg.append('g').attr('class','scalebar').attr('pointer-events','none');
  sb.append('rect').attr('x',bx).attr('y',by-1).attr('width',bw).attr('height',2).attr('fill',sc);
  sb.append('rect').attr('x',bx).attr('y',by-4).attr('width',1).attr('height',7).attr('fill',sc);
  sb.append('rect').attr('x',bx+bw-1).attr('y',by-4).attr('width',1).attr('height',7).attr('fill',sc);
  sb.append('text').attr('x',bx+bw/2).attr('y',by-7)
    .attr('text-anchor','middle').attr('font-size',8)
    .attr('font-family','IBM Plex Mono,monospace').attr('fill',sc).text('~660 km');
}

/* ── Public API ───────────────────────────────────────────── */
return { build, setLayer, zoomIn, zoomOut, resetView, closePanel, updateTheme, drawScaleBar };

})();
