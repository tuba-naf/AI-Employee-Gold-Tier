"""
Facebook Post — Gold Tier AI Employee
Auto-posts approved Facebook drafts to a Facebook Page via Meta Graph API.

Workflow:
  1. Read FACEBOOK_*.md from /Vault/Approved/
  2. Extract post content (strip frontmatter, use Draft Content section)
  3. POST to https://graph.facebook.com/v19.0/{page_id}/feed
  4. On success: move file to /Vault/Completed/, log action
  5. On failure: leave in /Vault/Approved/, log error

Environment variables required (add to .env):
  FB_PAGE_ID          — Your Facebook Page ID (numeric)
  FB_PAGE_ACCESS_TOKEN — Long-lived Page Access Token from Meta Developer Console
  AUTO_POST_FACEBOOK  — "true" to auto-post verified drafts without HITL (default: false)
  DRY_RUN             — "true" to log only, never post live
"""

import os
import re
import json
import logging
import requests
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("FacebookPost")

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
AUTO_POST_FACEBOOK = os.getenv("AUTO_POST_FACEBOOK", "false").lower() == "true"

GRAPH_API_URL = "https://graph.facebook.com/v19.0"
MAX_DRAFTS_PER_RUN = int(os.getenv("MAX_DRAFTS_PER_RUN", "1"))


def get_approved_facebook_drafts() -> list[Path]:
    """Return approved Facebook drafts from /Vault/Approved/."""
    approved_dir = VAULT_PATH / "Approved"
    if not approved_dir.exists():
        return []
    return sorted(
        f for f in approved_dir.iterdir()
        if f.suffix == ".md" and f.name.upper().startswith("FACEBOOK_")
    )


def get_auto_eligible_drafts() -> list[Path]:
    """Return verified Facebook drafts from /Needs_Action/ eligible for auto-posting."""
    needs_action = VAULT_PATH / "Needs_Action"
    if not needs_action.exists():
        return []
    eligible = []
    for f in needs_action.iterdir():
        if not (f.suffix == ".md" and f.name.upper().startswith("FACEBOOK_")):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            if "status: verified" in content and "auto_post_eligible: true" in content:
                eligible.append(f)
        except OSError:
            continue
    return sorted(eligible)


def extract_post_content(filepath: Path) -> str:
    """Strip frontmatter and return only the Draft Content section."""
    text = filepath.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].strip()
    match = re.search(r"^## Draft Content\s*\n", text, re.MULTILINE)
    if match:
        content_start = match.end()
        next_section = re.search(r"^## ", text[content_start:], re.MULTILINE)
        if next_section:
            return text[content_start:content_start + next_section.start()].strip()
        return text[content_start:].strip()
    return text.strip()


def post_to_facebook(content: str) -> dict:
    """POST content to the Facebook Page feed via Graph API."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        raise ValueError(
            "Facebook posting not configured. "
            "Set FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN in .env"
        )

    url = f"{GRAPH_API_URL}/{FB_PAGE_ID}/feed"
    payload = {
        "message": content,
        "access_token": FB_PAGE_ACCESS_TOKEN,
    }
    response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def move_to_approved(filepath: Path) -> Path:
    """Move an auto-eligible draft from /Needs_Action/ to /Approved/."""
    approved_dir = VAULT_PATH / "Approved"
    approved_dir.mkdir(exist_ok=True)
    dest = approved_dir / filepath.name
    content = filepath.read_text(encoding="utf-8")
    content = re.sub(r"^(status:\s*).*$", r"\1approved", content, count=1, flags=re.MULTILINE)
    dest.write_text(content, encoding="utf-8")
    filepath.unlink()
    logger.info(f"Auto-moved to /Approved/: {filepath.name}")
    return dest


def move_to_completed(filepath: Path, post_id: str = ""):
    """Move posted draft to /Vault/Completed/ and stamp status as posted."""
    completed_dir = VAULT_PATH / "Completed"
    completed_dir.mkdir(exist_ok=True)
    dest = completed_dir / filepath.name
    content = filepath.read_text(encoding="utf-8")
    content = re.sub(r"^(status:\s*).*$", r"\1posted", content, count=1, flags=re.MULTILINE)
    if post_id:
        content += f"\n\n## Post Result\n- **Facebook Post ID:** {post_id}\n- **Posted At:** {datetime.now().isoformat()}\n"
    dest.write_text(content, encoding="utf-8")
    filepath.unlink()
    logger.info(f"Moved to /Completed/: {filepath.name}")


def log_action(filepath: Path, result: str, post_id: str = "", error: str = ""):
    """Append action to today's audit log."""
    logs_dir = VAULT_PATH / "Logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entries = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []
    entries.append({
        "timestamp": datetime.now().isoformat(),
        "action_type": "facebook_post",
        "actor": "facebook_post_script",
        "target": filepath.name,
        "parameters": {"dry_run": DRY_RUN, "auto_post": AUTO_POST_FACEBOOK},
        "result": result,
        "post_id": post_id,
        "error": error,
    })
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def main():
    drafts = []

    # Auto-post path: move verified auto-eligible drafts to Approved then post
    if AUTO_POST_FACEBOOK:
        auto_drafts = get_auto_eligible_drafts()
        for draft in auto_drafts[:MAX_DRAFTS_PER_RUN]:
            approved = move_to_approved(draft)
            drafts.append(approved)

    # Standard path: post anything already in /Approved/
    approved_drafts = get_approved_facebook_drafts()
    for d in approved_drafts:
        if d not in drafts:
            drafts.append(d)

    drafts = drafts[:MAX_DRAFTS_PER_RUN]

    if not drafts:
        logger.info("No Facebook drafts ready to post.")
        return

    logger.info(f"Found {len(drafts)} Facebook draft(s) to post")

    for draft in drafts:
        content = extract_post_content(draft)
        if not content:
            logger.warning(f"Empty content in {draft.name} — skipping.")
            log_action(draft, "skipped_empty_content")
            continue

        if DRY_RUN:
            logger.info(f"[DRY RUN] Would post to Facebook Page {FB_PAGE_ID}: {draft.name}")
            logger.info(f"  Content preview: {content[:150]}...")
            log_action(draft, "dry_run")
            continue

        try:
            result = post_to_facebook(content)
            post_id = result.get("id", "")
            logger.info(f"Posted to Facebook: {draft.name} (post_id: {post_id})")
            move_to_completed(draft, post_id)
            log_action(draft, "success", post_id=post_id)
        except ValueError as e:
            logger.error(f"Facebook not configured: {e}")
            log_action(draft, "not_configured", error=str(e))
            break
        except requests.HTTPError as e:
            logger.error(f"Facebook API error for {draft.name}: {e}")
            log_action(draft, "api_error", error=str(e))
        except Exception as e:
            logger.error(f"Failed to post {draft.name}: {e}")
            log_action(draft, "failure", error=str(e))


if __name__ == "__main__":
    main()
