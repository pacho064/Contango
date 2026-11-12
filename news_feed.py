"""
Contango Energy — latest headlines -> data/news-feed.json

Headlines only: title as the outlet wrote it, link to the outlet, outlet name,
publication time. No summaries, no rewriting, no analysis, no AI.

Sources (free, no keys):
  Al Jazeera       official RSS            aljazeera.com/xml/rss/all.xml
  The New York Times official RSS          rss.nytimes.com ... MiddleEast.xml, World.xml
  Tasnim (Iran)    official English RSS    tasnimnews.ir/en/rss  (CC BY 4.0)
  Reuters          no public RSS exists -> Google News RSS restricted to reuters.com
  Al Mayadeen      no RSS found          -> Google News RSS restricted to its domain
  ISW / CTP        no RSS found          -> Google News RSS restricted to its domains
Each source lists candidate feeds in order; the first that yields usable items
wins. Items from Google News are kept only if the publisher domain Google reports
matches the outlet, so an unrelated site can never appear under an outlet's name.

Run locally:
    python3 news_feed.py
    python3 -m http.server 8000      # then open http://localhost:8000

Editorial rules this script follows:
  - Titles are published as written (HTML entities decoded, trailing " - Outlet"
    removed). Nothing is summarised or reworded.
  - Every item carries its outlet, the outlet's own publication time and a link.
  - Items without a parseable time are dropped, never given a guessed one.
  - An item is kept only if its title names the region/topic (Hormuz, Bab
    el-Mandeb, Red Sea/Houthis, Suez, Iran, the Gulf states/Iraq, OPEC).
  - Inclusion of an outlet is not an endorsement or verification of its claims.
  - A single failed source is logged as a warning and recorded in the file; if no
    source yields anything, the script exits non-zero (the GitHub Action turns
    red) and the previous file is left untouched.
"""

import os, re, sys, json, time, html, datetime, urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

OUT_PATH = Path("data/news-feed.json")
KEEP_DAYS = 7
DAILY_KEEP_DAYS = 14
MAX_PER_SOURCE = 25
MAX_ITEMS = 100
TIMEOUT = 25
UA = "ContangoEnergy/1.0 (+https://contango-energy.com)"

TOPIC_TERMS = '(Hormuz OR Iran OR "Red Sea" OR Houthi OR "Persian Gulf" OR "Bab el-Mandeb" OR OPEC OR Saudi OR Iraq)'


def gnews(query):
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(query)
            + "&hl=en-US&gl=US&ceid=US:en")


def gnews_pair(domain, extra=None):
    q = extra if extra else TOPIC_TERMS
    return [gnews(f"site:{domain} {q} when:2d"), gnews(f"allinurl:{domain} {q} when:2d")]


SOURCES = [
    {"id": "aljazeera", "name": "Al Jazeera", "origin": "Qatar", "domains": ["aljazeera.com"],
     "feeds": ["https://www.aljazeera.com/xml/rss/all.xml"] + gnews_pair("aljazeera.com")},
    {"id": "nyt", "name": "The New York Times", "origin": "US", "domains": ["nytimes.com"],
     "feeds": ["https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",
               "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"] + gnews_pair("nytimes.com")},
    {"id": "reuters", "name": "Reuters", "origin": "UK", "domains": ["reuters.com"],
     "feeds": gnews_pair("reuters.com")},
    {"id": "tasnim", "name": "Tasnim News Agency", "origin": "Iran",
     "domains": ["tasnimnews.ir", "tasnimnews.com"],
     "feeds": ["https://www.tasnimnews.ir/en/rss"] + gnews_pair("tasnimnews.ir", "(Hormuz OR Gulf OR oil OR sanctions OR navy)")},
    {"id": "almayadeen", "name": "Al Mayadeen", "origin": "Lebanon", "domains": ["almayadeen.net"],
     "feeds": gnews_pair("almayadeen.net")},
    {"id": "ctp", "name": "ISW / CTP", "origin": "US",
     "domains": ["criticalthreats.org", "understandingwar.org", "iswresearch.org"],
     "feeds": ["https://www.criticalthreats.org/feed",
               gnews('site:criticalthreats.org "Iran Update" when:7d'),
               gnews('site:understandingwar.org "Iran Update" when:7d'),
               gnews('allinurl:criticalthreats.org/analysis/iran-update when:7d')]},
]

TAGS = {
    "hormuz": r"hormuz",
    "bab_el_mandeb": r"bab[\s\-]*(?:el|al)[\s\-]*mandeb|mandab",
    "red_sea": r"red sea|houthi|ansar allah",
    "suez": r"\bsuez\b",
    "iran": r"\biran|irgc|revolutionary guard|tehran|khamenei|pezeshkian|araghchi",
    "gulf": r"persian gulf|gulf of oman|arabian gulf|\bgulf\b|saudi|aramco|kuwait|qatar|\buae\b|emirat|\boman\b|bahrain|\biraq|basra|kurdistan",
    "opec": r"\bopec",
}
TAGS_RE = {k: re.compile(v, re.I) for k, v in TAGS.items()}
RELEVANT = ("hormuz", "bab_el_mandeb", "red_sea", "suez", "iran", "gulf", "opec")
DAILY_RE = re.compile(r"iran update", re.I)


def warn(msg):
    print("WARNING: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg.replace("\n", " "))


def url_map():
    p = os.environ.get("NEWS_URL_MAP")      # test hook: {"real url": "local url"}
    if p:
        try:
            return json.loads(Path(p).read_text())
        except Exception:
            return {}
    return {}


def http_get(url):
    real = url_map().get(url, url)
    req = urllib.request.Request(real, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    last = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read(6_000_000)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code < 500 and e.code != 429:
                break
        except Exception as e:
            last = str(e)[:100]
        time.sleep(2)
    raise RuntimeError(last or "request failed")


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def child_text(el, name):
    for c in el:
        if local(c.tag) == name:
            return (c.text or "").strip()
    return ""


def parse_time(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        d = None
    if d is None:
        try:
            d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone.utc)


def host_of(u):
    try:
        return (urllib.parse.urlparse(u).hostname or "").lower()
    except Exception:
        return ""


def domain_ok(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)


def clean_title(t, outlet_names):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    for n in outlet_names:            # Google appends " - Outlet"
        suf = " - " + n
        if t.lower().endswith(suf.lower()):
            t = t[: -len(suf)].rstrip()
    return t


def parse_feed(raw, src, via_google):
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise RuntimeError(f"not valid XML ({e})")
    nodes = [e for e in root.iter() if local(e.tag) in ("item", "entry")]
    items, seen = [], len(nodes)
    names = [src["name"], src["name"].split(" / ")[0], "Reuters", "The New York Times", "Al Jazeera"]
    for n in nodes:
        title = child_text(n, "title")
        link = child_text(n, "link")
        if not link:                                   # Atom
            for c in n:
                if local(c.tag) == "link" and c.get("href"):
                    link = c.get("href"); break
        when = parse_time(child_text(n, "pubDate") or child_text(n, "published") or child_text(n, "updated") or child_text(n, "date"))
        if not (title and link and when) or not link.startswith(("http://", "https://")):
            continue
        extra_names = []
        if via_google:
            pub = ""
            for c in n:
                if local(c.tag) == "source":
                    pub = host_of(c.get("url", ""))
                    if (c.text or "").strip():
                        extra_names.append(c.text.strip())
            if not domain_ok(pub, src["domains"]):
                continue
        else:
            if not domain_ok(host_of(link), src["domains"]):
                continue
        items.append({"t": when, "title": clean_title(title, names + extra_names), "url": link})
    return items, seen


def tag_item(title):
    return [k for k, rx in TAGS_RE.items() if rx.search(title)]


def collect(src, now):
    status = {"id": src["id"], "name": src["name"], "origin": src["origin"], "status": "failed",
              "feed_used": None, "items_seen": 0, "items_kept": 0, "error": None}
    errors = []
    for feed in src["feeds"]:
        via_google = feed.startswith("https://news.google.com/")
        try:
            items, seen = parse_feed(http_get(feed), src, via_google)
        except Exception as e:
            errors.append(f"{feed[:70]}…: {e}")
            continue
        status["items_seen"] = seen
        if not items:
            errors.append(f"{feed[:70]}…: no usable items")
            continue
        keep, daily_cut = [], now - datetime.timedelta(days=DAILY_KEEP_DAYS)
        cut = now - datetime.timedelta(days=KEEP_DAYS)
        for it in items:
            it["tags"] = tag_item(it["title"])
            is_daily = src["id"] == "ctp" and DAILY_RE.search(it["title"])
            if is_daily and it["t"] >= daily_cut:
                it["daily"] = True
                keep.append(it); continue
            if it["t"] >= cut and any(t in RELEVANT for t in it["tags"]):
                keep.append(it)
        keep.sort(key=lambda x: x["t"], reverse=True)
        keep = keep[:MAX_PER_SOURCE]
        status.update(status="ok" if keep else "no_relevant_items", feed_used=feed, items_kept=len(keep), error=None)
        return keep, status
    status["error"] = "; ".join(errors)[:400]
    return [], status


def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    all_items, statuses = [], []
    for src in SOURCES:
        items, st = collect(src, now)
        for it in items:
            it["source"] = src["id"]; it["source_name"] = src["name"]; it["origin"] = src["origin"]
        all_items += items
        statuses.append(st)
        if st["status"] == "failed":
            warn(f"{src['name']}: no feed worked. {st['error']}")
        else:
            print(f"  {src['name']}: {st['items_kept']} kept of {st['items_seen']} via {st['feed_used'][:60]}…")

    if not all_items:
        print("ERROR: no source produced any usable headline.", file=sys.stderr)
        sys.exit(1)

    # de-duplicate: same outlet + same normalised title, or same link
    seen_k, seen_u, uniq = set(), set(), []
    for it in sorted(all_items, key=lambda x: x["t"], reverse=True):
        k = (it["source"], re.sub(r"\W+", " ", it["title"].lower()).strip())
        if k in seen_k or it["url"] in seen_u:
            continue
        seen_k.add(k); seen_u.add(it["url"]); uniq.append(it)

    daily = [i for i in uniq if i.get("daily")][:3]
    general = [i for i in uniq if not i.get("daily")][:MAX_ITEMS]

    def out_item(i):
        return {"t": i["t"].strftime("%Y-%m-%dT%H:%M:%SZ"), "source": i["source"], "source_name": i["source_name"],
                "origin": i["origin"], "title": i["title"], "url": i["url"], "tags": i["tags"]}

    body = {"sources": statuses, "daily_updates": [out_item(i) for i in daily], "items": [out_item(i) for i in general]}

    existing = {}
    if OUT_PATH.exists():
        try:
            existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    if {k: v for k, v in existing.items() if not k.startswith("_")} == body:
        print("No change since last run - file left as is.")
        return
    out = {
        "_note": "Written by news_feed.py. Headlines, links and times belong to the named outlets; Contango adds no analysis. Inclusion is not endorsement or verification.",
        "_updated": now.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.update(body)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {OUT_PATH}: {len(general)} headlines, {len(daily)} ISW/CTP daily updates, "
          f"{sum(1 for s in statuses if s['status']=='failed')} source(s) failed")


if __name__ == "__main__":
    main()
