"""
Contango Energy — automated news intelligence updater
Runs via GitHub Actions daily at 06:00 UTC (before market open).

Pipeline:
  1. Fetch last 24hrs of Gulf energy articles from GDELT (free, no key)
  2. Fetch full article text for top results
  3. Call Claude Haiku to extract structured facts (pure extraction, no opinion)
  4. Deduplicate against existing events.json timeline
  5. Append new high-confidence entries to events.json
  6. Commit to repo

Required GitHub secret: ANTHROPIC_API_KEY
No other API keys required.

GDELT is a global event database that indexes news in near-real-time.
Documentation: https://blog.gdeltproject.org/gdelt-2-0-our-successor-to-gdelt-1-0/
"""

import os, json, sys, datetime, time, hashlib, re
import urllib.request, urllib.parse, urllib.error
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

EVENTS_PATH = Path("data/events.json")

# How many hours back to search for news
LOOKBACK_HOURS = 28  # slightly more than 24 to avoid gaps

# Minimum confidence score (0-1) to add an entry
MIN_CONFIDENCE = 0.75

# Max new entries per run (prevent runaway costs)
MAX_NEW_ENTRIES = 8

# Claude model for extraction (Haiku is cheapest, sufficient for extraction)
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# Keywords for GDELT query — Gulf energy focused
GDELT_KEYWORDS = [
    "Hormuz",
    "Strait of Hormuz",
    "Iran oil",
    "Iran blockade",
    "Iran nuclear",
    "Saudi Aramco production",
    "Saudi Arabia oil",
    "Iraq SOMO oil",
    "OPEC production",
    "Brent crude",
    "crude oil disruption",
    "tanker attack Gulf",
    "Persian Gulf oil",
]

# Tags assigned by keyword match (for page-level filtering)
TAG_RULES = {
    "hormuz": ["hormuz", "strait"],
    "iran": ["iran", "iranian", "irgc", "tehran"],
    "saudi_arabia": ["saudi", "aramco", "riyadh", "yanbu", "ras tanura", "east-west pipeline"],
    "iraq": ["iraq", "iraqi", "somo", "basra", "rumaila"],
    "uae": ["uae", "adnoc", "murban", "fujairah", "abu dhabi"],
    "kuwait": ["kuwait", "kpc"],
    "qatar": ["qatar", "qatarenergie", "ras laffan"],
    "opec": ["opec", "quota", "compliance"],
    "prices": ["brent", "wti", "crude price", "oil price", "barrel"],
    "tankers": ["tanker", "vlcc", "shipping", "vessel", "ship"],
    "diplomatic": ["ceasefire", "talks", "negotiations", "deal", "agreement", "sanction"],
}


# ── GDELT fetch ─────────────────────────────────────────────────────────────────

def gdelt_search(query: str, hours_back: int = 28) -> list[dict]:
    """
    Search GDELT for recent articles.
    Returns list of {url, title, date, domain} dicts.
    """
    # GDELT GKG 2.0 Article Search API
    # https://api.gdeltproject.org/api/v2/doc/doc
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": "25",
        "timespan": f"{hours_back}h",
        "format": "json",
        "sort": "DateDesc",
    }
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ContangoEnergy/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        articles = data.get("articles", [])
        return [
            {
                "url": a.get("url", ""),
                "title": a.get("title", ""),
                "date": a.get("seendate", ""),
                "domain": a.get("domain", ""),
                "language": a.get("language", ""),
            }
            for a in articles
            if a.get("language", "English") == "English"
            and a.get("url", "")
        ]
    except Exception as e:
        print(f"  GDELT search failed: {e}", file=sys.stderr)
        return []


def fetch_article_text(url: str, max_chars: int = 3000) -> str:
    """Fetch article body text. Returns truncated plain text."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; ContangoBot/1.0; +https://pacho064.github.io/Contango/)",
                "Accept": "text/html,application/xhtml+xml",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read(50000).decode("utf-8", errors="ignore")

        # Very basic HTML strip
        raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()

        # Find the most text-dense section
        words = raw.split()
        if len(words) > 800:
            # Take a middle chunk that's likely the article body
            start = len(words) // 6
            chunk = " ".join(words[start:start + 600])
        else:
            chunk = " ".join(words[:600])

        return chunk[:max_chars]
    except Exception as e:
        return ""


# ── Claude extraction ───────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are a data extraction assistant for an oil market intelligence database.

Extract ONLY verifiable facts stated explicitly in the article below.
Do NOT infer, predict, editorialize, or add information not in the article.
Do NOT include opinions or forecasts unless they are attributed to a named source with a specific number.

Article title: {title}
Article domain: {domain}
Article date: {date}

Article text:
{text}

---

If this article contains a significant, new, verifiable development related to:
- Strait of Hormuz transit disruption or reopening
- Iran military/diplomatic actions affecting oil
- Saudi Arabia, Iraq, UAE, Kuwait, Qatar oil production or infrastructure
- OPEC production figures (with specific numbers)
- Named oil price forecasts with specific numbers from named institutions
- Tanker attacks, seizures, or blockades
- Diplomatic talks or agreements affecting oil flows

Then extract one timeline entry as JSON. Otherwise return {{"skip": true, "reason": "brief reason"}}.

JSON format (if extracting):
{{
  "date": "DD Mon YYYY",
  "type": "critical|important|context",
  "src": "Named source(s) from article · Date",
  "hl": "One sentence factual headline. No opinion. Max 120 chars.",
  "detail": "2-3 sentences. Only facts stated in article. Name sources for numbers. Max 400 chars.",
  "numbers": [{{"val": "numeric value with unit", "lbl": "what it measures"}}],
  "tags": ["tag1", "tag2"],
  "confidence": 0.0,
  "article_url": "{url}"
}}

Rules for fields:
- date: Use the article's publication date
- type: "critical" = major disruption/attack/blockade; "important" = significant development; "context" = background
- src: Always name the publication and date. E.g. "Reuters · 7 May 2026"  
- hl: Start with the subject. No "breaking:" prefixes. Facts only.
- detail: If a number is mentioned, include it and its source. No passive voice.
- numbers: Only include if specific numeric values are in the article (bpd, $, %, mb). Max 3.
- tags: Choose from: hormuz, iran, saudi_arabia, iraq, uae, kuwait, qatar, opec, prices, tankers, diplomatic
- confidence: Your confidence this is genuinely new, significant, and accurately extracted (0.0-1.0)

Respond with ONLY valid JSON. No markdown, no explanation."""


def claude_extract(article: dict, text: str) -> dict | None:
    """
    Call Claude Haiku to extract a structured timeline entry from article text.
    Returns extracted entry dict, or None if skipped/failed.
    """
    if not ANTHROPIC_API_KEY:
        print("  ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return None

    prompt = EXTRACTION_PROMPT.format(
        title=article.get("title", ""),
        domain=article.get("domain", ""),
        date=article.get("date", ""),
        text=text[:3000],
        url=article.get("url", ""),
    )

    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        raw = resp["content"][0]["text"].strip()

        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

        extracted = json.loads(raw)

        if extracted.get("skip"):
            return None

        return extracted

    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}", file=sys.stderr)
        return None
    except urllib.error.HTTPError as e:
        print(f"  Claude API error: {e.code} {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Extraction error: {e}", file=sys.stderr)
        return None


# ── Deduplication ───────────────────────────────────────────────────────────────

def entry_fingerprint(entry: dict) -> str:
    """Create a stable hash for deduplication."""
    # Use date + first 60 chars of headline
    key = f"{entry.get('date','')}-{entry.get('hl','')[:60]}"
    return hashlib.md5(key.lower().encode()).hexdigest()[:12]


def is_duplicate(new_entry: dict, existing_entries: list[dict]) -> bool:
    """Check if a new entry is too similar to existing ones."""
    new_fp = entry_fingerprint(new_entry)
    new_hl = new_entry.get("hl", "").lower()

    for existing in existing_entries:
        # Exact fingerprint match
        if entry_fingerprint(existing) == new_fp:
            return True
        # High word overlap in headline
        existing_hl = existing.get("hl", "").lower()
        new_words = set(new_hl.split())
        existing_words = set(existing_hl.split())
        if len(new_words) > 3 and len(existing_words) > 3:
            overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
            if overlap > 0.6:
                return True
        # Same date + similar detail
        if existing.get("date") == new_entry.get("date"):
            new_detail = new_entry.get("detail", "").lower()[:100]
            ex_detail = existing.get("detail", "").lower()[:100]
            if new_detail and ex_detail and new_detail[:50] == ex_detail[:50]:
                return True

    return False


# ── Tag inference ───────────────────────────────────────────────────────────────

def infer_tags(entry: dict) -> list[str]:
    """Infer tags from entry content if not provided."""
    text = (entry.get("hl", "") + " " + entry.get("detail", "")).lower()
    tags = set(entry.get("tags", []))
    for tag, keywords in TAG_RULES.items():
        for kw in keywords:
            if kw in text:
                tags.add(tag)
                break
    return sorted(tags)


# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Exiting.", file=sys.stderr)
        sys.exit(1)

    if not EVENTS_PATH.exists():
        print(f"ERROR: {EVENTS_PATH} not found. Run from repo root.", file=sys.stderr)
        sys.exit(1)

    events = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    existing_timeline = events.get("timeline", [])
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    print(f"Contango news updater — {today}")
    print(f"Existing timeline entries: {len(existing_timeline)}")

    # ── Step 1: Gather candidate articles from GDELT ──
    print("\nFetching GDELT articles...")
    all_articles = []
    seen_urls = set()

    # Run a few targeted queries
    queries = [
        "Hormuz oil tanker",
        "Iran crude oil blockade",
        "Saudi Arabia Aramco production disruption",
        "Iraq SOMO oil output",
        "OPEC crude production",
        "Gulf oil crisis ceasefire",
    ]

    for q in queries:
        articles = gdelt_search(q, hours_back=LOOKBACK_HOURS)
        for a in articles:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)
        time.sleep(0.5)  # Be polite to GDELT

    print(f"Found {len(all_articles)} unique articles")

    # Filter to likely relevant domains
    PREFERRED_DOMAINS = {
        "reuters.com", "bloomberg.com", "ft.com", "wsj.com",
        "cnbc.com", "aljazeera.com", "bbc.com", "apnews.com",
        "oilprice.com", "argus media", "platts", "spglobal.com",
        "energyintel.com", "mees.com", "arabnews.com", "zawya.com",
        "khaleejtimes.com", "thenationalnews.com", "middleeasteye.net",
        "axios.com", "politico.com", "thehill.com",
    }

    def domain_score(a):
        domain = a.get("domain", "").lower()
        for d in PREFERRED_DOMAINS:
            if d in domain:
                return 2
        return 1

    all_articles.sort(key=domain_score, reverse=True)

    # ── Step 2: Extract structured entries via Claude ──
    print("\nExtracting intelligence from articles...")
    new_entries = []
    processed = 0
    costs_approx = 0.0

    for article in all_articles:
        if len(new_entries) >= MAX_NEW_ENTRIES:
            break
        if processed >= 30:  # Safety cap on API calls
            break

        title = article.get("title", "")
        url = article.get("url", "")

        # Quick keyword pre-filter — skip obviously irrelevant
        title_lower = title.lower()
        relevant_kws = ["hormuz", "iran", "saudi", "aramco", "iraq", "opec",
                        "crude", "brent", "tanker", "gulf", "blockade", "ceasefire",
                        "somo", "adnoc", "kpc", "qatarenergie"]
        if not any(kw in title_lower for kw in relevant_kws):
            continue

        print(f"  Processing: {title[:70]}...")

        # Fetch article text
        text = fetch_article_text(url)
        if len(text) < 200:
            print(f"    Skipped (too short or failed to fetch)")
            continue

        processed += 1
        costs_approx += 0.0003  # ~$0.0003 per Haiku call estimate

        # Extract via Claude
        entry = claude_extract(article, text)

        if entry is None:
            print(f"    Skipped by extraction")
            continue

        confidence = entry.get("confidence", 0)
        if confidence < MIN_CONFIDENCE:
            print(f"    Low confidence ({confidence:.2f}) — skipped")
            continue

        # Enrich tags
        entry["tags"] = infer_tags(entry)

        # Deduplicate
        if is_duplicate(entry, existing_timeline):
            print(f"    Duplicate — skipped")
            continue

        # Add metadata
        entry["_auto"] = True
        entry["_extracted"] = today
        entry["_source_url"] = url

        print(f"    ✓ Added: [{entry.get('type','?')}] {entry.get('hl','')[:60]}... (conf: {confidence:.2f})")
        new_entries.append(entry)

        time.sleep(0.3)  # Avoid hammering Claude API

    # ── Step 3: Merge and save ──
    print(f"\nNew entries: {len(new_entries)} (processed {processed} articles, ~${costs_approx:.3f} API cost)")

    if not new_entries:
        print("No new entries — events.json unchanged.")
        # Update the _news_checked timestamp even if no new entries
        events["_news_checked"] = today
        EVENTS_PATH.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
        return

    # Insert new entries at the top of timeline (most recent first)
    # Sort by date if possible, else just prepend
    events["timeline"] = new_entries + existing_timeline
    events["_news_checked"] = today
    events["_updated"] = today

    EVENTS_PATH.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {EVENTS_PATH} with {len(events['timeline'])} total timeline entries")
    print("\nGit commands:")
    print("  git add data/events.json")
    print(f"  git commit -m 'intelligence: {len(new_entries)} new entries {today}'")
    print("  git push")


if __name__ == "__main__":
    main()
