"""
Gmail Watcher — Gold Tier AI Employee (Personal Domain)
Monitors Gmail inbox for urgent/important emails and creates action files in the vault.

Workflow:
  1. Connect to Gmail via Google Gmail API (OAuth2)
  2. Fetch unread emails matching urgency criteria
  3. Save structured .md files to /Vault/Inbox/ for Claude to triage
  4. Claude reads, categorises, drafts replies → /Vault/Needs_Action/

STATUS: STRUCTURE READY — requires Gmail API OAuth2 credentials
Setup:
  1. Go to console.cloud.google.com
  2. Create a project → enable Gmail API
  3. Create OAuth 2.0 credentials (Desktop app)
  4. Download credentials JSON → save as gmail_credentials.json in Watchers/
  5. Run once manually to generate token.json (browser auth flow)
  6. Set GMAIL_CHECK_INTERVAL in .env (default: 300 seconds)

Environment variables:
  GMAIL_CREDENTIALS_FILE  — path to credentials JSON (default: Watchers/gmail_credentials.json)
  GMAIL_TOKEN_FILE        — path to saved OAuth token (default: Watchers/gmail_token.json)
  GMAIL_CHECK_INTERVAL    — polling interval in seconds (default: 300)
  GMAIL_MAX_RESULTS       — max emails to fetch per run (default: 10)
  VAULT_PATH              — path to Obsidian vault
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GmailWatcher")

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
CREDENTIALS_FILE = Path(os.getenv("GMAIL_CREDENTIALS_FILE", os.path.join(os.path.dirname(__file__), "gmail_credentials.json")))
TOKEN_FILE = Path(os.getenv("GMAIL_TOKEN_FILE", os.path.join(os.path.dirname(__file__), "gmail_token.json")))
CHECK_INTERVAL = int(os.getenv("GMAIL_CHECK_INTERVAL", "300"))
MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "10"))

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Track processed message IDs to avoid duplicates
SEEN_IDS_FILE = Path(os.path.dirname(__file__)) / "gmail_seen_ids.json"


def _load_seen_ids() -> set:
    if SEEN_IDS_FILE.exists():
        try:
            return set(json.loads(SEEN_IDS_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def _save_seen_ids(ids: set):
    # Keep last 500 IDs to prevent file bloat
    ids_list = list(ids)[-500:]
    SEEN_IDS_FILE.write_text(json.dumps(ids_list), encoding="utf-8")


def _get_gmail_service():
    """Authenticate and return Gmail API service."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        logger.error("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return None

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                logger.error(f"Gmail credentials file not found: {CREDENTIALS_FILE}")
                logger.error("Download from console.cloud.google.com → APIs → Gmail API → Credentials")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    try:
        from googleapiclient.discovery import build
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        logger.error(f"Failed to build Gmail service: {e}")
        return None


def _extract_email_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail message payload."""
    import base64

    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_email_body(part)
        if result:
            return result
    return ""


def _create_inbox_file(msg_id: str, sender: str, subject: str, body: str, received_at: str) -> Path:
    """Create a structured .md file in /Vault/Inbox/ for an email."""
    inbox_dir = VAULT_PATH / "Inbox"
    inbox_dir.mkdir(exist_ok=True)

    short_hash = hashlib.md5(msg_id.encode()).hexdigest()[:8]
    filename = f"EMAIL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{short_hash}.md"
    filepath = inbox_dir / filename

    # Truncate body to avoid huge files
    body_preview = body[:1500].strip() if body else "(no body)"
    if len(body) > 1500:
        body_preview += "\n\n[... truncated — see Gmail for full message ...]"

    content = f"""---
type: email
source: gmail
message_id: {msg_id}
sender: {sender}
subject: {subject}
received_at: {received_at}
status: inbox
created: {datetime.now().isoformat()}
---

# Email: {subject}

**From:** {sender}
**Received:** {received_at}

## Body

{body_preview}

## Suggested Actions

- [ ] Reply
- [ ] Archive / No action needed
- [ ] Flag for follow-up
- [ ] Escalate
"""
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"Created inbox file: {filename}")
    return filepath


def run_once():
    """Fetch new emails and create inbox files. Returns number of new items processed."""
    service = _get_gmail_service()
    if not service:
        logger.warning("Gmail service unavailable — skipping run")
        return 0

    seen_ids = _load_seen_ids()

    try:
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=MAX_RESULTS,
        ).execute()
    except Exception as e:
        logger.error(f"Failed to list Gmail messages: {e}")
        return 0

    messages = results.get("messages", [])
    if not messages:
        logger.info("No new unread messages.")
        return 0

    new_count = 0
    for msg_ref in messages:
        msg_id = msg_ref["id"]
        if msg_id in seen_ids:
            continue

        try:
            msg = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
        except Exception as e:
            logger.error(f"Failed to fetch message {msg_id}: {e}")
            continue

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        sender = headers.get("From", "unknown")
        subject = headers.get("Subject", "(no subject)")
        date_str = headers.get("Date", datetime.now(timezone.utc).isoformat())

        body = _extract_email_body(msg.get("payload", {}))
        _create_inbox_file(msg_id, sender, subject, body, date_str)

        seen_ids.add(msg_id)
        new_count += 1

    _save_seen_ids(seen_ids)
    logger.info(f"Processed {new_count} new email(s).")
    return new_count


def run():
    """Continuous polling loop."""
    import time
    logger.info(f"Gmail Watcher started — polling every {CHECK_INTERVAL}s")
    while True:
        try:
            run_once()
        except Exception as e:
            logger.error(f"Unexpected error in Gmail watcher loop: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        count = run_once()
        print(f"Done. {count} new email(s) processed.")
    else:
        run()
