"""
Fetches RSS feeds from food science / analytical chemistry journals
and writes news.json for the digital signage display.
Runs via GitHub Actions every 2 hours — no CORS issues.
"""

import feedparser
import json
import re
import urllib.parse
from datetime import datetime, timezone
from html.parser import HTMLParser


# ── Figure URL construction ────────────────────────────────────────────────
def springer_fig1_url(article_url: str, year: int) -> str:
    """Construct the Springer Nature CDN URL for Fig1 from an article URL.

    Nature article URL pattern: .../articles/s{journal}-{yy}-{num}-{check}
    CDN pattern: media.springernature.com/m685/springer-static/image/
                 art%3A{encoded_doi}/MediaObjects/{journal}_{year}_{num}_Fig1_HTML.png
    """
    m = re.search(r'nature\.com/articles/(s(\d+)-\d+-0*(\d+)-\d+)', article_url)
    if not m:
        return ""
    suffix    = m.group(1)          # s43016-026-01368-3
    journal   = m.group(2)          # 43016
    art_num   = int(m.group(3))     # 1368 (leading zeros stripped)
    doi       = f"10.1038/{suffix}"
    enc       = urllib.parse.quote(f"art:{doi}", safe="")
    return (f"https://media.springernature.com/m685/springer-static/image/"
            f"{enc}/MediaObjects/{journal}_{year}_{art_num}_Fig1_HTML.png")

FEEDS = [
    {"url": "https://www.nature.com/natfood.rss",
     "name": "Nature Food"},
    {"url": "https://rss.sciencedirect.com/publication/science/03088146",
     "name": "Food Chemistry"},
    {"url": "https://rss.sciencedirect.com/publication/science/09242244",
     "name": "Trends in Food Science & Technology"},
    {"url": "https://rss.sciencedirect.com/publication/science/09503293",
     "name": "Food Quality & Preference"},
]

MAX_PER_FEED = 4   # article cards shown in slideshow
SUMMARY_MAX  = 300 # characters for the abstract snippet


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def get_text(self):
        return " ".join(self.result)


def strip_html(html: str) -> str:
    s = HTMLStripper()
    try:
        s.feed(html or "")
    except Exception:
        return ""
    text = s.get_text()
    return re.sub(r"\s+", " ", text).strip()


def clean_summary(raw: str) -> str:
    """Remove boilerplate RSS metadata, keep meaningful content."""
    raw = raw.strip()

    # Nature: "Nature Food, Published online: DATE; doi:DOI ACTUAL TEXT"
    m = re.search(r'doi:\S+\s+(.*)', raw, re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()

    # Elsevier: "Publication date: ... Source: ... Author(s): NAMES"
    if raw.startswith("Publication date:"):
        # Extract author names as the useful part
        m2 = re.search(r'Author\(s\):\s*(.+)', raw)
        if m2:
            authors = m2.group(1).strip()
            # Keep only first 3 authors
            parts = [a.strip() for a in authors.split(",") if a.strip()][:3]
            return "Authors: " + ", ".join(parts)
        return ""

    return raw


items = []
current_year = datetime.now(timezone.utc).year

for feed_info in FEEDS:
    is_nature = "nature.com" in feed_info["url"]
    try:
        feed = feedparser.parse(feed_info["url"])
        count = 0
        for entry in feed.entries:
            if count >= MAX_PER_FEED:
                break
            title = strip_html((entry.get("title") or "")).strip()
            if not title:
                continue

            article_url = entry.get("link", "")

            # Build summary from best available field
            raw_summary = ""
            for field in ("summary", "description", "content"):
                raw = ""
                if field == "content" and hasattr(entry, "content"):
                    raw = entry.content[0].get("value", "") if entry.content else ""
                else:
                    raw = entry.get(field, "")
                if raw:
                    raw_summary = strip_html(raw)
                    break

            summary = clean_summary(raw_summary)
            if len(summary) > SUMMARY_MAX:
                summary = summary[:SUMMARY_MAX - 3] + "..."

            # Build Fig1 URL from DOI (Nature only; no HTTP request needed)
            image = ""
            if is_nature and article_url:
                image = springer_fig1_url(article_url, current_year)

            items.append({
                "title":    title,
                "summary":  summary,
                "feedName": feed_info["name"],
                "url":      article_url,
                "image":    image,
            })
            count += 1

        print(f"  {feed_info['name']}: {count} articles")

    except Exception as e:
        print(f"  ERROR {feed_info['name']}: {e}")

result = {
    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "items":   items,
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\nDone — news.json: {len(items)} items")
