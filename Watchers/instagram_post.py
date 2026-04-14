"""
Instagram Post — Gold Tier AI Employee
Auto-posts approved Instagram drafts to an Instagram Business Account
via the Meta Graph API (two-step: create container, then publish).

This requires an Instagram Business or Creator account linked to a Facebook Page.

Workflow:
  1. Read INSTA_*.md from /Vault/Approved/
  2. Extract caption content
  3. Step 1: POST /{ig-user-id}/media  → creates a media container (image_url required for photos)
  4. Step 2: POST /{ig-user-id}/media_publish  → publishes the container
  5. On success: move file to /Vault/Completed/, log action
  6. On failure: leave in /Vault/Approved/, log error

Note: Text-only posts (CAPTION_ONLY) use the "REELS" or "CAROUSEL" workaround.
For simplicity this implementation posts as a text-only update using a placeholder image
URL, or skips the media step if IG_IMAGE_URL is not set (logs as needs_image).

Environment variables required (add to .env):
  IG_USER_ID           — Instagram Business User ID (numeric)
  IG_PAGE_ACCESS_TOKEN — Long-lived Page Access Token (same token as FB if linked)
  IG_DEFAULT_IMAGE_URL — Publicly accessible image URL for posts (required by Graph API)
  AUTO_POST_INSTAGRAM  — "true" to auto-post verified drafts without HITL (default: false)
  DRY_RUN              — "true" to log only, never post live
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
logger = logging.getLogger("InstagramPost")

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_PAGE_ACCESS_TOKEN = os.getenv("IG_PAGE_ACCESS_TOKEN", "")
IG_DEFAULT_IMAGE_URL = os.getenv("IG_DEFAULT_IMAGE_URL", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
AUTO_POST_INSTAGRAM = os.getenv("AUTO_POST_INSTAGRAM", "false").lower() == "true"

GRAPH_API_URL = "https://graph.facebook.com/v19.0"
MAX_DRAFTS_PER_RUN = int(os.getenv("MAX_DRAFTS_PER_RUN", "1"))


def get_approved_instagram_drafts() -> list[Path]:
    approved_dir = VAULT_PATH / "Approved"
    if not approved_dir.exists():
        return []
    return sorted(
        f for f in approved_dir.iterdir()
        if f.suffix == ".md" and f.name.upper().startswith("INSTA_")
    )


def get_auto_eligible_drafts() -> list[Path]:
    needs_action = VAULT_PATH / "Needs_Action"
    if not needs_action.exists():
        return []
    eligible = []
    for f in needs_action.iterdir():
        if not (f.suffix == ".md" and f.name.upper().startswith("INSTA_")):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            if "status: verified" in content and "auto_post_eligible: true" in content:
                eligible.append(f)
        except OSError:
            continue
    return sorted(eligible)


def extract_post_content(filepath: Path) -> str:
    """Strip frontmatter and return the Draft Content section."""
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


def create_media_container(caption: str, image_url: str) -> str:
    """Step 1: Create an Instagram media container. Returns container_id."""
    url = f"{GRAPH_API_URL}/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_PAGE_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()
    return resp.json().get("id", "")


def publish_media_container(container_id: str) -> dict:
    """Step 2: Publish an Instagram media container. Returns API response."""
    url = f"{GRAPH_API_URL}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": IG_PAGE_ACCESS_TOKEN,
    }
    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def move_to_approved(filepath: Path) -> Path:
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
    completed_dir = VAULT_PATH / "Completed"
    completed_dir.mkdir(exist_ok=True)
    dest = completed_dir / filepath.name
    content = filepath.read_text(encoding="utf-8")
    content = re.sub(r"^(status:\s*).*$", r"\1posted", content, count=1, flags=re.MULTILINE)
    if post_id:
        content += f"\n\n## Post Result\n- **Instagram Post ID:** {post_id}\n- **Posted At:** {datetime.now().isoformat()}\n"
    dest.write_text(content, encoding="utf-8")
    filepath.unlink()
    logger.info(f"Moved to /Completed/: {filepath.name}")


def log_action(filepath: Path, result: str, post_id: str = "", error: str = ""):
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
        "action_type": "instagram_post",
        "actor": "instagram_post_script",
        "target": filepath.name,
        "parameters": {"dry_run": DRY_RUN, "auto_post": AUTO_POST_INSTAGRAM},
        "result": result,
        "post_id": post_id,
        "error": error,
    })
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def main():
    drafts = []

    if AUTO_POST_INSTAGRAM:
        auto_drafts = get_auto_eligible_drafts()
        for draft in auto_drafts[:MAX_DRAFTS_PER_RUN]:
            approved = move_to_approved(draft)
            drafts.append(approved)

    for d in get_approved_instagram_drafts():
        if d not in drafts:
            drafts.append(d)

    drafts = drafts[:MAX_DRAFTS_PER_RUN]

    if not drafts:
        logger.info("No Instagram drafts ready to post.")
        return

    logger.info(f"Found {len(drafts)} Instagram draft(s) to post")

    for draft in drafts:
        content = extract_post_content(draft)
        if not content:
            logger.warning(f"Empty content in {draft.name} — skipping.")
            log_action(draft, "skipped_empty_content")
            continue

        if DRY_RUN:
            logger.info(f"[DRY RUN] Would post to Instagram @{IG_USER_ID}: {draft.name}")
            logger.info(f"  Content preview: {content[:150]}...")
            log_action(draft, "dry_run")
            continue

        if not IG_USER_ID or not IG_PAGE_ACCESS_TOKEN:
            logger.error("Instagram credentials not configured.")
            log_action(draft, "not_configured", error="IG_USER_ID or IG_PAGE_ACCESS_TOKEN missing")
            break

        if not IG_DEFAULT_IMAGE_URL:
            logger.warning(f"{draft.name}: IG_DEFAULT_IMAGE_URL not set — Instagram requires an image. Skipping.")
            log_action(draft, "needs_image", error="IG_DEFAULT_IMAGE_URL not configured in .env")
            continue

        try:
            container_id = create_media_container(content, IG_DEFAULT_IMAGE_URL)
            if not container_id:
                raise RuntimeError("Empty container_id returned from media creation step.")

            result = publish_media_container(container_id)
            post_id = result.get("id", "")
            logger.info(f"Posted to Instagram: {draft.name} (post_id: {post_id})")
            move_to_completed(draft, post_id)
            log_action(draft, "success", post_id=post_id)

        except requests.HTTPError as e:
            logger.error(f"Instagram API error for {draft.name}: {e}")
            log_action(draft, "api_error", error=str(e))
        except Exception as e:
            logger.error(f"Failed to post {draft.name}: {e}")
            log_action(draft, "failure", error=str(e))


if __name__ == "__main__":
    main()
