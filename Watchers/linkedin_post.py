"""
LinkedIn Post — Stub for future LinkedIn API posting.

STATUS: NOT IMPLEMENTED
This script is a structural placeholder. Actual posting requires:
  - LinkedIn OAuth 2.0 app credentials (Client ID + Secret)
  - Access token with w_member_social scope
  - LinkedIn API endpoint: POST /ugcPosts

Workflow (when implemented):
  1. Read approved draft from /Vault/Approved/
  2. Extract post content (strip frontmatter, use Draft Content section)
  3. POST to LinkedIn API
  4. On success: move file to /Vault/Completed/, log action
  5. On failure: leave in /Vault/Approved/, log error

Environment variables needed (add to .env):
  LINKEDIN_CLIENT_ID=
  LINKEDIN_CLIENT_SECRET=
  LINKEDIN_ACCESS_TOKEN=
  LINKEDIN_AUTHOR_URN=urn:li:person:<your-person-id>
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("LinkedInPost")

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Silver-Tier/Vault"))
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN = os.getenv("LINKEDIN_AUTHOR_URN", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

LINKEDIN_API_URL = "https://api.linkedin.com/v2/ugcPosts"


def get_approved_linkedin_drafts() -> list[Path]:
    """Return approved LinkedIn drafts from /Vault/Approved/."""
    approved_dir = VAULT_PATH / "Approved"
    if not approved_dir.exists():
        return []
    return sorted(
        f for f in approved_dir.iterdir()
        if f.suffix == ".md" and f.name.upper().startswith("LINKEDIN_")
    )


def extract_post_content(filepath: Path) -> str:
    """Strip frontmatter and return only the Draft Content section."""
    text = filepath.read_text(encoding="utf-8")
    # Strip frontmatter
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].strip()
    # Extract Draft Content section
    import re
    match = re.search(r"^## Draft Content\s*\n", text, re.MULTILINE)
    if match:
        content_start = match.end()
        next_section = re.search(r"^## ", text[content_start:], re.MULTILINE)
        if next_section:
            return text[content_start:content_start + next_section.start()].strip()
        return text[content_start:].strip()
    return text.strip()


def post_to_linkedin(content: str) -> dict:
    """
    POST content to LinkedIn API.
    NOT IMPLEMENTED — raises NotImplementedError until credentials are configured.
    """
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_AUTHOR_URN:
        raise NotImplementedError(
            "LinkedIn posting not configured. "
            "Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN in .env"
        )

    # TODO: implement when LinkedIn OAuth credentials are available
    # import requests
    # payload = {
    #     "author": LINKEDIN_AUTHOR_URN,
    #     "lifecycleState": "PUBLISHED",
    #     "specificContent": {
    #         "com.linkedin.ugc.ShareContent": {
    #             "shareCommentary": {"text": content},
    #             "shareMediaCategory": "NONE",
    #         }
    #     },
    #     "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    # }
    # headers = {
    #     "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
    #     "Content-Type": "application/json",
    #     "X-Restli-Protocol-Version": "2.0.0",
    # }
    # response = requests.post(LINKEDIN_API_URL, json=payload, headers=headers)
    # response.raise_for_status()
    # return response.json()

    raise NotImplementedError("LinkedIn posting not yet implemented")


def move_to_completed(filepath: Path):
    """Move posted draft to /Vault/Completed/."""
    completed_dir = VAULT_PATH / "Completed"
    completed_dir.mkdir(exist_ok=True)
    dest = completed_dir / filepath.name
    import re
    content = filepath.read_text(encoding="utf-8")
    content = re.sub(r"^(status:\s*).*$", r"\1posted", content, count=1, flags=re.MULTILINE)
    dest.write_text(content, encoding="utf-8")
    filepath.unlink()
    logger.info(f"Moved to /Completed/: {filepath.name}")


def log_action(filepath: Path, result: str, error: str = ""):
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
        "action_type": "linkedin_post",
        "actor": "linkedin_post_script",
        "target": filepath.name,
        "parameters": {"dry_run": DRY_RUN},
        "result": result,
        "error": error,
    })
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def main():
    drafts = get_approved_linkedin_drafts()
    if not drafts:
        logger.info("No approved LinkedIn drafts found.")
        return

    logger.info(f"Found {len(drafts)} approved LinkedIn draft(s)")

    for draft in drafts:
        content = extract_post_content(draft)
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would post to LinkedIn: {draft.name}")
            logger.info(f"  Content preview: {content[:120]}...")
            log_action(draft, "dry_run")
            continue

        try:
            post_to_linkedin(content)
            logger.info(f"Posted to LinkedIn: {draft.name}")
            move_to_completed(draft)
            log_action(draft, "success")
        except NotImplementedError as e:
            logger.error(f"LinkedIn posting not implemented: {e}")
            log_action(draft, "not_implemented", str(e))
            break
        except Exception as e:
            logger.error(f"Failed to post {draft.name}: {e}")
            log_action(draft, "failure", str(e))


if __name__ == "__main__":
    main()
