"""
Twitter Watcher — Gold Tier AI Employee
Generates content drafts for Twitter/X.
Monitors trending topics via RSS feeds and generates Pakistan-focused content
following the rotation: Local Problem -> Local Hopeful -> Global Problem -> Global Hopeful.

Twitter format: short, punchy, thread-friendly (280 chars per tweet).
Drafts are saved as TWITTER_*.md in /Inbox/ for verification before posting.

STATUS: STRUCTURE READY
Requires Twitter API v2 credentials to post.
Draft generation works without Twitter credentials (uses OpenAI only).
"""

import os
import hashlib
import logging
from pathlib import Path
from datetime import datetime

import feedparser
from dotenv import load_dotenv
from base_watcher import BaseWatcher, is_environment_relevant, is_article_fresh

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# --- Pakistan-only feeds (for local_problem / local_hopeful) ---
LOCAL_FEEDS = [
    "https://feeds.dawn.com/feed/",
    "https://www.geo.tv/rss/1/1",
    "https://tribune.com.pk/feed/home",
]

# --- International feeds (for global_problem / global_hopeful) ---
GLOBAL_FEEDS = [
    "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",
    "https://www.theguardian.com/environment/rss",
    "https://news.un.org/feed/subscribe/en/news/topic/climate-change/feed/rss.xml",
]

LOCAL_KEYWORDS = [
    "pakistan", "lahore", "karachi", "islamabad", "punjab", "sindh",
    "smog", "pollution", "flood", "drought", "glacier", "indus",
    "deforestation", "billion tree", "clean green", "water crisis",
    "climate", "environment", "renewable", "solar", "wind energy",
    "mangrove", "waste", "plastic", "air quality", "monsoon",
]

GLOBAL_KEYWORDS = [
    "climate", "climate change", "global warming", "sustainability",
    "renewable", "solar", "wind energy", "clean energy", "fossil fuel",
    "carbon", "emission", "greenhouse", "net zero", "paris agreement",
    "pollution", "deforestation", "biodiversity", "conservation",
    "flood", "drought", "glacier", "sea level", "heat wave", "wildfire",
]


class TwitterWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        check_interval = int(os.getenv("TWITTER_CHECK_INTERVAL", "14400"))
        super().__init__(vault_path, platform="twitter", check_interval=check_interval)

    def _get_feeds_and_keywords(self):
        cycle = self.current_cycle_position
        if cycle in ("local_problem", "local_hopeful"):
            return LOCAL_FEEDS, LOCAL_KEYWORDS
        return GLOBAL_FEEDS, GLOBAL_KEYWORDS

    def check_for_updates(self) -> list:
        feeds, keywords = self._get_feeds_and_keywords()
        cycle = self.current_cycle_position
        items = []

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:50]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    link = entry.get("link", "")
                    published = entry.get("published", "")
                    combined = f"{title} {summary}"
                    if is_environment_relevant(combined) and is_article_fresh(entry):
                        item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                        if item_id not in self.state.get("processed_ids", []):
                            items.append({
                                "id": item_id,
                                "title": title,
                                "summary": summary,
                                "link": link,
                                "published": published,
                                "source": feed_url,
                                "scope": "local" if "local" in cycle else "global",
                            })
            except Exception as e:
                self.logger.warning(f"Failed to fetch feed {feed_url}: {e}")

        # Fallback to global if no local articles
        if not items and cycle in ("local_problem", "local_hopeful"):
            self.logger.info(f"No local articles for {cycle}, falling back to global feeds")
            for feed_url in GLOBAL_FEEDS:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:50]:
                        title = entry.get("title", "")
                        summary = entry.get("summary", entry.get("description", ""))
                        link = entry.get("link", "")
                        published = entry.get("published", "")
                        combined = f"{title} {summary}"
                        if is_environment_relevant(combined):
                            item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                            if item_id not in self.state.get("processed_ids", []):
                                items.append({
                                    "id": item_id,
                                    "title": title,
                                    "summary": summary,
                                    "link": link,
                                    "published": published,
                                    "source": feed_url,
                                    "scope": "local",
                                })
                except Exception as e:
                    self.logger.warning(f"Fallback feed failed {feed_url}: {e}")

        return items[:1] if items else []

    def create_content_file(self, item) -> Path | None:
        cycle = self.current_cycle_position
        draft_content = self.generate_draft_content(
            item, cycle, "Twitter", self._get_cycle_instructions(cycle), 280
        )
        if draft_content is None:
            self.logger.error(f"Skipping draft for '{item['title']}' — content generation failed.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TWITTER_{timestamp}_{item['id']}.md"
        filepath = self.inbox / filename

        content = f"""---
platform: Twitter
status: pending
cycle_type: {cycle}
scope: {item.get('scope', 'local')}
source_title: "{item['title']}"
source_link: {item['link']}
source_published: "{item['published']}"
created: {datetime.now().isoformat()}
word_target: 280
auto_post_eligible: false
---

# Twitter Draft — {cycle.replace('_', ' ').title()}

## Source Reference
- **Title:** {item['title']}
- **Link:** {item['link']}
- **Scope:** {item.get('scope', 'local').upper()} (Pakistan-focused)

## Content Instructions
Write a **Twitter thread** (3-5 tweets, 280 chars each) following the **{cycle.replace('_', ' ').title()}** pattern.

### Requirements:
{self._get_cycle_instructions(cycle)}

## Draft Content

{draft_content}

## Verification Checklist
- [ ] Each tweet is under 280 characters
- [ ] Facts and statistics are accurate
- [ ] Pakistan context is highlighted
- [ ] Thread flows naturally from tweet to tweet
- [ ] Ends with a call to action or question
- [ ] Hashtags included in last tweet

## Suggested Hashtags
#Pakistan #ClimateAction #Sustainability #Environment #GreenPakistan

---
*Generated by Twitter Watcher v1.0 — Gold Tier*
"""
        filepath.write_text(content, encoding="utf-8")
        self.state.setdefault("processed_ids", []).append(item["id"])
        self.state["processed_ids"] = self.state["processed_ids"][-200:]
        self._save_state()
        self.logger.info(f"Twitter draft created: {filename} (cycle: {cycle})")
        return filepath

    def _get_cycle_instructions(self, cycle: str) -> str:
        instructions = {
            "local_problem": """- Highlight a current environmental problem in Pakistan in tweet 1
- Add facts/data in tweets 2-3
- Connect to human impact in tweet 4
- End with a question to drive engagement in tweet 5
- Keep each tweet under 280 characters""",
            "local_hopeful": """- Lead with a positive sustainability story from Pakistan in tweet 1
- Share key impact numbers in tweets 2-3
- Inspire action in tweet 4
- End with a shareable call to action in tweet 5
- Keep each tweet under 280 characters""",
            "global_problem": """- Open with a striking global climate fact in tweet 1
- Connect to Pakistan's situation in tweet 2
- Add data and context in tweets 3-4
- End with why this matters locally in tweet 5
- Keep each tweet under 280 characters""",
            "global_hopeful": """- Lead with an exciting global green innovation in tweet 1
- Explain the breakthrough in tweets 2-3
- Connect to Pakistan's potential in tweet 4
- End with an inspiring call to action in tweet 5
- Keep each tweet under 280 characters""",
        }
        return instructions.get(cycle, "Follow the content rotation pattern.")


if __name__ == "__main__":
    vault = os.getenv("VAULT_PATH", "./Vault")
    watcher = TwitterWatcher(vault)
    watcher.run()
