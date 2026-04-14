"""
Facebook Watcher - Generates content drafts for a Facebook Page.
Monitors trending topics via RSS feeds and generates Pakistan-focused content
following the rotation: Local Problem -> Local Hopeful -> Global Problem -> Global Hopeful.

LOCAL cycles only use Pakistan feeds + Pakistan keywords.
GLOBAL cycles only use international feeds + global keywords.
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
    "balochistan", "kpk", "khyber", "peshawar", "quetta", "faisalabad",
    "smog", "pollution", "flood", "drought", "glacier", "indus",
    "deforestation", "billion tree", "clean green", "thar", "tharparkar",
    "water crisis", "water scarcity", "heatwave", "heat wave",
    "climate", "environment", "renewable", "solar", "wind energy",
    "mangrove", "waste", "plastic", "air quality", "monsoon",
    "forest", "wildlife", "biodiversity", "conservation", "sustainable",
    "carbon", "emission", "green", "energy", "coal", "recycling",
    "reforestation", "afforestation", "ecosystem", "ecological",
]

GLOBAL_KEYWORDS = [
    "climate", "climate change", "global warming", "sustainability",
    "renewable", "solar", "wind energy", "clean energy", "fossil fuel",
    "carbon", "emission", "greenhouse", "net zero", "paris agreement", "cop",
    "pollution", "air quality", "deforestation", "reforestation", "biodiversity",
    "conservation", "wildlife", "endangered", "ecosystem",
    "flood", "drought", "glacier", "sea level", "heat wave", "wildfire",
    "water scarcity", "desertification", "ozone", "mangrove", "wetland",
    "recycling", "waste", "circular economy", "sustainable development",
    "electric vehicle", "green energy", "environment", "ecological",
    "coral", "ocean", "plastic", "ice melt", "arctic", "antarctic",
]


class FacebookWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        check_interval = int(os.getenv("FACEBOOK_CHECK_INTERVAL", "14400"))
        super().__init__(vault_path, platform="facebook", check_interval=check_interval)

    def _get_feeds_and_keywords(self):
        """Return feeds and keywords based on current cycle position."""
        cycle = self.current_cycle_position
        if cycle in ("local_problem", "local_hopeful"):
            return LOCAL_FEEDS, LOCAL_KEYWORDS
        else:
            return GLOBAL_FEEDS, GLOBAL_KEYWORDS

    def check_for_updates(self) -> list:
        """Scan RSS feeds for trending topics relevant to Facebook posts."""
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

        # Fallback: if no local articles found, use global feeds
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
                    self.logger.warning(f"Failed to fetch feed {feed_url}: {e}")

        return items[:1] if items else []

    def create_content_file(self, item) -> Path | None:
        """Create a Facebook draft .md file in /Inbox/. Returns None if generation fails."""
        cycle = self.current_cycle_position
        draft_content = self.generate_draft_content(
            item, cycle, "Facebook", self._get_cycle_instructions(cycle), 400
        )
        if draft_content is None:
            self.logger.error(f"Skipping draft for '{item['title']}' — content generation failed.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FACEBOOK_{timestamp}_{item['id']}.md"
        filepath = self.inbox / filename

        content = f"""---
platform: Facebook
status: pending
cycle_type: {cycle}
scope: {item.get('scope', 'local')}
source_title: "{item['title']}"
source_link: {item['link']}
source_published: "{item['published']}"
created: {datetime.now().isoformat()}
word_target: 400
auto_post_eligible: false
---

# Facebook Draft — {cycle.replace('_', ' ').title()}

## Source Reference
- **Title:** {item['title']}
- **Summary:** {item['summary']}
- **Link:** {item['link']}
- **Scope:** {item.get('scope', 'local').upper()} (Pakistan-focused)

## Content Instructions
Write a **400+ word** Facebook post following the **{cycle.replace('_', ' ').title()}** pattern.

### Requirements:
{self._get_cycle_instructions(cycle)}

## Draft Content

{draft_content}

## Verification Checklist
- [ ] Facts and statistics are accurate and cited
- [ ] Pakistan context is highlighted
- [ ] Tone is engaging and shareable
- [ ] Word count meets 400+ target
- [ ] Sources and references are verifiable
- [ ] Ends with a question or call-to-action to drive comments

## Suggested Hashtags
#Pakistan #ClimateAction #Sustainability #Environment #GreenPakistan #ClimateChange #RenewableEnergy

---
*Generated by Facebook Watcher v1.0 — Gold Tier*
"""
        filepath.write_text(content, encoding="utf-8")
        self.state.setdefault("processed_ids", []).append(item["id"])
        self.state["processed_ids"] = self.state["processed_ids"][-200:]
        self._save_state()
        self.logger.info(f"Facebook draft created: {filename} (cycle: {cycle}, scope: {item.get('scope')})")
        return filepath

    def _get_cycle_instructions(self, cycle: str) -> str:
        instructions = {
            "local_problem": """- Highlight a **current environmental or climate problem in Pakistan**
- Focus on: air pollution, water scarcity, deforestation, flooding, glacial melt, or waste crisis
- Include **facts, figures**, and credible references (Pakistan EPA, UNDP, WHO)
- Mention affected communities and human impact
- Use an empathetic, awareness-raising tone appropriate for Facebook
- End with a question to the audience to encourage comments
- ALL content must be directly about Pakistan""",
            "local_hopeful": """- Showcase **green solutions or sustainability success stories in Pakistan**
- Highlight renewable energy projects, Billion Tree Tsunami, clean water programs, or eco-startups
- Include measurable impact (trees planted, MW installed, communities helped)
- Use an uplifting, inspiring tone
- End with a shareable call-to-action
- ALL content must be directly about Pakistan""",
            "global_problem": """- Highlight a **trending global environmental or climate crisis**
- Connect its **relevance to Pakistan's situation**
- Include IPCC data or UN reports
- Show how global climate trends affect Pakistan (floods, heat waves, glacial melt)
- Keep it accessible and shareable for a general Facebook audience""",
            "global_hopeful": """- Showcase **global green innovations or climate breakthroughs**
- Explain how they could **inspire action in Pakistan**
- Highlight transferable clean energy, conservation, or circular economy strategies
- Make it optimistic and forward-looking
- End with an actionable takeaway or question for Pakistani readers""",
        }
        return instructions.get(cycle, "Follow the content rotation pattern.")


if __name__ == "__main__":
    vault = os.getenv("VAULT_PATH", "./Vault")
    watcher = FacebookWatcher(vault)
    watcher.run()
