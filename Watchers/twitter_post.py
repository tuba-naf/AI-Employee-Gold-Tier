"""
Twitter Post — Gold Tier AI Employee
Posts approved Twitter drafts to Twitter/X via Twitter API v2.

Workflow:
  1. Read TWITTER_*.md from /Vault/Approved/
  2. Extract tweet thread content
  3. POST each tweet via Twitter API v2 (POST /2/tweets)
  4. On success: move file to /Vault/Completed/, log action
  5. On failure: leave in /Vault/Approved/, log error

Thread handling:
  Drafts contain multiple tweets separated by "---" or numbered (1/, 2/, etc.)
  Each tweet is posted as a reply to the previous one to form a thread.

STATUS: STRUCTURE READY — requires Twitter API v2 credentials
Environment variables required (add to .env):
  TWITTER_API_KEY            — API Key (Consumer Key)
  TWITTER_API_SECRET         — API Key Secret (Consumer Secret)
  TWITTER_ACCESS_TOKEN       — Access Token
  TWITTER_ACCESS_TOKEN_SECRET — Access Token Secret
  TWITTER_BEARER_TOKEN       — Bearer Token (for read operations)
  AUTO_POST_TWITTER          — "true" to auto-post verified drafts (default: false)
  DRY_RUN                    — "true" to log only, never post live
"""

import os
import re
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
logger = logging.getLogger("TwitterPost")

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
AUTO_POST_TWITTER = os.getenv("AUTO_POST_TWITTER", "false").lower() == "true"
MAX_DRAFTS_PER_RUN = int(os.getenv("MAX_DRAFTS_PER_RUN", "1"))

TWITTER_API_URL = "https://api.twitter.com/2/tweets"


def get_twitter_client():
    """Return an authenticated tweepy Client. Raises if credentials missing."""
    try:
        import tweepy
    except ImportError:
        raise ImportError("tweepy not installed. Run: pip install tweepy")

    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        raise ValueError(
            "Twitter credentials not configured. "
            "Set TWITTER_API_KEY, TWITTER_API_SECRET, "
            "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET in .env"
        )

    return tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )


def get_approved_twitter_drafts() -> list[Path]:
    approved_dir = VAULT_PATH / "Approved"
    if not approved_dir.exists():
        return []
    return sorted(
        f for f in approved_dir.iterdir()
        if f.suffix == ".md" and f.name.upper().startswith("TWITTER_")
    )


def get_auto_eligible_drafts() -> list[Path]:
    needs_action = VAULT_PATH / "Needs_Action"
    if not needs_action.exists():
        return []
    eligible = []
    for f in needs_action.iterdir():
        if not (f.suffix == ".md" and f.name.upper().startswith("TWITTER_")):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            if "status: verified" in content and "auto_post_eligible: true" in content:
                eligible.append(f)
        except OSError:
            continue
    return sorted(eligible)


def extract_tweets(filepath: Path) -> list[str]:
    """
    Extract individual tweets from the Draft Content section.
    Splits on numbered tweets (1/, 2/) or "---" separators.
    Each tweet trimmed to 280 characters max.
    """
    text = filepath.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].strip()

    match = re.search(r"^## Draft Content\s*\n", text, re.MULTILINE)
    if match:
        start = match.end()
        nxt = re.search(r"^## ", text[start:], re.MULTILINE)
        content = text[start:start + nxt.start()].strip() if nxt else text[start:].strip()
    else:
        content = text.strip()

    # Split by numbered tweet markers (1/, 2/, etc.) or --- separators
    tweets = re.split(r"\n(?:\d+/|\-{3,})\s*\n", content)
    tweets = [t.strip() for t in tweets if t.strip()]

    # Also try splitting by lines starting with a number + /
    if len(tweets) == 1:
        tweets = re.split(r"(?m)^\d+/\s*", content)
        tweets = [t.strip() for t in tweets if t.strip()]

    # Trim each tweet to 280 chars
    return [t[:280] for t in tweets if t]


def post_thread(tweets: list[str]) -> list[str]:
    """Post a list of tweets as a thread. Returns list of tweet IDs."""
    client = get_twitter_client()
    tweet_ids = []
    reply_to_id = None

    for tweet_text in tweets:
        params = {"text": tweet_text}
        if reply_to_id:
            params["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        response = client.create_tweet(**params)
        tweet_id = response.data["id"]
        tweet_ids.append(tweet_id)
        reply_to_id = tweet_id

    return tweet_ids


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


def move_to_completed(filepath: Path, tweet_ids: list[str]):
    completed_dir = VAULT_PATH / "Completed"
    completed_dir.mkdir(exist_ok=True)
    dest = completed_dir / filepath.name
    content = filepath.read_text(encoding="utf-8")
    content = re.sub(r"^(status:\s*).*$", r"\1posted", content, count=1, flags=re.MULTILINE)
    content += f"\n\n## Post Result\n- **Tweet IDs:** {', '.join(tweet_ids)}\n- **Posted At:** {datetime.now().isoformat()}\n"
    dest.write_text(content, encoding="utf-8")
    filepath.unlink()
    logger.info(f"Moved to /Completed/: {filepath.name}")


def log_action(filepath: Path, result: str, tweet_ids: list = None, error: str = ""):
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
        "action_type": "twitter_post",
        "actor": "twitter_post_script",
        "target": filepath.name,
        "parameters": {"dry_run": DRY_RUN, "auto_post": AUTO_POST_TWITTER},
        "result": result,
        "tweet_ids": tweet_ids or [],
        "error": error,
    })
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def main():
    drafts = []

    if AUTO_POST_TWITTER:
        for draft in get_auto_eligible_drafts()[:MAX_DRAFTS_PER_RUN]:
            drafts.append(move_to_approved(draft))

    for d in get_approved_twitter_drafts():
        if d not in drafts:
            drafts.append(d)

    drafts = drafts[:MAX_DRAFTS_PER_RUN]

    if not drafts:
        logger.info("No Twitter drafts ready to post.")
        return

    logger.info(f"Found {len(drafts)} Twitter draft(s) to post")

    for draft in drafts:
        tweets = extract_tweets(draft)
        if not tweets:
            logger.warning(f"No tweets extracted from {draft.name} — skipping.")
            log_action(draft, "skipped_empty_content")
            continue

        if DRY_RUN:
            logger.info(f"[DRY RUN] Would post {len(tweets)}-tweet thread to Twitter: {draft.name}")
            for i, t in enumerate(tweets, 1):
                logger.info(f"  Tweet {i}: {t[:80]}...")
            log_action(draft, "dry_run")
            continue

        try:
            tweet_ids = post_thread(tweets)
            logger.info(f"Posted {len(tweet_ids)}-tweet thread: {draft.name}")
            move_to_completed(draft, tweet_ids)
            log_action(draft, "success", tweet_ids=tweet_ids)
        except ImportError as e:
            logger.error(f"tweepy not installed: {e}")
            log_action(draft, "missing_dependency", error=str(e))
            break
        except ValueError as e:
            logger.error(f"Twitter not configured: {e}")
            log_action(draft, "not_configured", error=str(e))
            break
        except Exception as e:
            logger.error(f"Failed to post {draft.name}: {e}")
            log_action(draft, "failure", error=str(e))


if __name__ == "__main__":
    main()
