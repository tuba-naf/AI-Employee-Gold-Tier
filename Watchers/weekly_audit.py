"""
Weekly Content Audit — Gold Tier AI Employee
Generates a Monday Morning Content Briefing by reading:
  - Vault/Logs/         — action audit logs (posts, verifications, errors)
  - Vault/Completed/    — verified/posted content counts per platform
  - Vault/Needs_Action/ — backlog of drafts waiting for review
  - Facebook Graph API  — engagement stats (reach, likes, comments, shares)
    on posts published this week via the Page feed

Output: /Vault/Briefings/YYYY-MM-DD_Content_Briefing.md

Run manually or via Windows Task Scheduler every Monday morning.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("WeeklyAudit")

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
GRAPH_API_URL = "https://graph.facebook.com/v19.0"

PLATFORM_PREFIXES = {
    "LINKEDIN_": "LinkedIn",
    "INSTA_": "Instagram",
    "NEWS_": "News",
    "FACEBOOK_": "Facebook",
}


# ── Vault helpers ─────────────────────────────────────────────────────────────

def get_week_range() -> tuple[datetime, datetime]:
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=7)
    return start, end


def read_logs_for_week(start: datetime) -> list[dict]:
    logs_dir = VAULT_PATH / "Logs"
    entries = []
    if not logs_dir.exists():
        return entries
    for i in range(8):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = logs_dir / f"{day}.json"
        if log_file.exists():
            try:
                entries.extend(json.loads(log_file.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
    return entries


def count_files_in(folder: str, start: datetime) -> dict[str, int]:
    """Count .md files per platform in a vault folder, modified since start."""
    target = VAULT_PATH / folder
    counts: dict[str, int] = defaultdict(int)
    if not target.exists():
        return counts
    for f in target.iterdir():
        if f.suffix != ".md":
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime >= start:
                for prefix, label in PLATFORM_PREFIXES.items():
                    if f.name.upper().startswith(prefix):
                        counts[label] += 1
        except OSError:
            pass
    return dict(counts)


def count_backlog() -> dict[str, int]:
    """Count drafts currently sitting in /Needs_Action/ (all time, not just this week)."""
    needs_action = VAULT_PATH / "Needs_Action"
    counts: dict[str, int] = defaultdict(int)
    if not needs_action.exists():
        return counts
    for f in needs_action.iterdir():
        if f.suffix != ".md":
            continue
        for prefix, label in PLATFORM_PREFIXES.items():
            if f.name.upper().startswith(prefix):
                counts[label] += 1
    return dict(counts)


def count_verification_results(entries: list[dict]) -> tuple[int, int]:
    """Return (verified_count, needs_review_count) from log entries."""
    verified = sum(1 for e in entries if e.get("result") == "success" and "verif" in e.get("action_type", ""))
    needs_review = sum(1 for e in entries if e.get("result") == "needs_review")
    return verified, needs_review


def get_errors(entries: list[dict]) -> list[dict]:
    return [
        e for e in entries
        if e.get("result") in ("failure", "api_error", "not_configured", "not_implemented")
    ]


def get_cycle_position() -> str:
    """Read the current content cycle position from the facebook watcher state."""
    for platform in ("facebook", "linkedin", "instagram", "news"):
        state_file = VAULT_PATH / "Watchers" / f".{platform}_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                cycle_map = ["Local Problem", "Local Hopeful", "Global Problem", "Global Hopeful"]
                idx = state.get("cycle_index", 0) % 4
                return cycle_map[idx]
            except (json.JSONDecodeError, OSError, KeyError):
                pass
    return "Unknown"


# ── Facebook Graph API ─────────────────────────────────────────────────────────

def get_facebook_engagement(days: int = 7) -> dict:
    """
    Fetch posts published in the last N days from the Facebook Page
    and return engagement stats (likes, comments, shares, reach).

    Returns a dict with:
      posts: list of {message, created_time, likes, comments, shares, reach}
      total_likes, total_comments, total_shares, total_reach
      best_post: the post with highest reach
    """
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        return {"error": "Facebook credentials not configured (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN missing in .env)"}

    since_ts = int((datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp())

    try:
        # Fetch recent posts with engagement fields
        url = f"{GRAPH_API_URL}/{FB_PAGE_ID}/posts"
        params = {
            "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
            "since": since_ts,
            "limit": 25,
            "access_token": FB_PAGE_ACCESS_TOKEN,
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        raw_posts = resp.json().get("data", [])

        posts = []
        total_likes = total_comments = total_shares = total_reach = 0

        for post in raw_posts:
            likes = post.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
            shares = post.get("shares", {}).get("count", 0) if post.get("shares") else 0
            message = (post.get("message") or "")[:120]
            created = post.get("created_time", "")[:10]

            # Fetch reach separately (requires page_read_engagement permission)
            reach = 0
            try:
                ins_url = f"{GRAPH_API_URL}/{post['id']}/insights/post_impressions_unique"
                ins_resp = requests.get(ins_url, params={"access_token": FB_PAGE_ACCESS_TOKEN}, timeout=15)
                if ins_resp.ok:
                    ins_data = ins_resp.json().get("data", [])
                    if ins_data:
                        reach = ins_data[0].get("values", [{}])[-1].get("value", 0)
            except Exception:
                pass  # reach is optional — don't fail the whole report

            total_likes += likes
            total_comments += comments
            total_shares += shares
            total_reach += reach

            posts.append({
                "message": message,
                "created_time": created,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "reach": reach,
            })

        best_post = max(posts, key=lambda p: p["reach"] or p["likes"], default=None)

        return {
            "posts": posts,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_reach": total_reach,
            "best_post": best_post,
        }

    except requests.HTTPError as e:
        return {"error": f"Facebook API HTTP error: {e}"}
    except Exception as e:
        return {"error": f"Facebook API error: {e}"}


# ── Report builder ─────────────────────────────────────────────────────────────

def build_fb_engagement_section(engagement: dict) -> str:
    if "error" in engagement:
        return f"_Could not fetch Facebook engagement: {engagement['error']}_"

    posts = engagement.get("posts", [])
    if not posts:
        return "_No Facebook posts found in the past 7 days._"

    lines = [
        f"- **Posts published:** {len(posts)}",
        f"- **Total Likes:** {engagement['total_likes']}",
        f"- **Total Comments:** {engagement['total_comments']}",
        f"- **Total Shares:** {engagement['total_shares']}",
        f"- **Total Reach:** {engagement['total_reach']:,}" if engagement['total_reach'] else "- **Total Reach:** _not available (requires pages_read_engagement permission)_",
    ]

    best = engagement.get("best_post")
    if best:
        lines += [
            "",
            "**Best Performing Post This Week:**",
            f"> \"{best['message']}...\"",
            f"> {best['created_time']} | Likes: {best['likes']} | Comments: {best['comments']} | Shares: {best['shares']}" + (f" | Reach: {best['reach']:,}" if best['reach'] else ""),
        ]

    lines.append("")
    lines.append("**All Posts:**")
    lines.append("| Date | Likes | Comments | Shares | Preview |")
    lines.append("|------|-------|----------|--------|---------|")
    for p in posts:
        preview = p["message"][:60].replace("|", "-")
        lines.append(f"| {p['created_time']} | {p['likes']} | {p['comments']} | {p['shares']} | {preview}... |")

    return "\n".join(lines)


def generate_briefing() -> Path:
    start, end = get_week_range()
    week_str = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    today_str = datetime.now().strftime("%Y-%m-%d")

    logger.info("Reading vault logs...")
    entries = read_logs_for_week(start)

    logger.info("Counting completed content...")
    completed = count_files_in("Completed", start)
    total_posts = sum(completed.values())

    logger.info("Counting backlog...")
    backlog = count_backlog()
    total_backlog = sum(backlog.values())

    errors = get_errors(entries)
    cycle_position = get_cycle_position()

    logger.info("Fetching Facebook engagement stats...")
    engagement = get_facebook_engagement(days=7)
    fb_section = build_fb_engagement_section(engagement)

    # Build completed table rows
    completed_rows = ""
    for label in ["LinkedIn", "Facebook", "Instagram", "News"]:
        count = completed.get(label, 0)
        backlog_count = backlog.get(label, 0)
        completed_rows += f"| {label:10} | {count:^10} | {backlog_count:^10} |\n"

    # Build error section
    if errors:
        error_lines = "\n".join(
            f"- [{e.get('timestamp','')[:16]}] `{e.get('action_type','')}` → "
            f"`{e.get('result','')}` — {str(e.get('error',''))[:80]}"
            for e in errors[:10]
        )
    else:
        error_lines = "- No errors this week."

    # Suggestions
    suggestions = []
    if total_backlog > 3:
        suggestions.append(f"- {total_backlog} drafts are sitting in /Needs_Action/ — consider reviewing or running the verification pipeline.")
    if errors:
        suggestions.append(f"- {len(errors)} error(s) occurred this week — check the Errors section and rotate API tokens if needed.")
    if not engagement.get("posts"):
        suggestions.append("- No Facebook posts detected this week — verify AUTO_POST_FACEBOOK=true and DRY_RUN=false in .env.")
    if not suggestions:
        suggestions.append("- Content pipeline running smoothly. No action required.")

    briefing = f"""---
generated: {datetime.now().isoformat()}
period: {week_str}
tier: Gold
type: Content Briefing
---

# Monday Morning Content Briefing
**Period:** {week_str}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## Content Output This Week
| Platform   | Published  | In Backlog |
|------------|------------|------------|
{completed_rows}
**Total published:** {total_posts} | **Total backlog:** {total_backlog}

---

## Content Cycle Status
- **Next post type:** {cycle_position}
- **Cycle:** Local Problem → Local Hopeful → Global Problem → Global Hopeful

---

## Facebook Page Engagement (Last 7 Days)
{fb_section}

---

## Errors & Failures
{error_lines}

---

## System Health
- **Log entries this week:** {len(entries)}
- **Errors this week:** {len(errors)}
- **Error rate:** {"0%" if not entries else f"{len(errors)/len(entries)*100:.1f}%"}

---

## Suggestions
{"".join(suggestions)}

---
*Generated by AI Employee Wavy v2.0 — Gold Tier*
"""

    briefings_dir = VAULT_PATH / "Briefings"
    briefings_dir.mkdir(exist_ok=True)
    output_file = briefings_dir / f"{today_str}_Content_Briefing.md"
    output_file.write_text(briefing, encoding="utf-8")
    logger.info(f"Content Briefing written: {output_file}")
    return output_file


def main():
    output = generate_briefing()
    print(f"Content Briefing generated: {output}")


if __name__ == "__main__":
    main()
