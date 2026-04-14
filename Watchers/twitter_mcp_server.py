"""
Twitter MCP Server — Gold Tier AI Employee
Exposes Twitter draft management and posting as MCP tools callable by Claude Code.

Tools:
  - list_twitter_drafts   : List pending/approved Twitter drafts in the vault
  - post_twitter_draft    : Post a specific approved draft as a thread to Twitter/X
  - get_timeline_summary  : Fetch recent tweets from the authenticated account (read-only)

STATUS: STRUCTURE READY — requires Twitter API v2 credentials in .env
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from mcp.server.fastmcp import FastMCP

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
AUTO_POST_TWITTER = os.getenv("AUTO_POST_TWITTER", "false").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

mcp = FastMCP("Gold Tier Twitter MCP")


def _credentials_configured() -> bool:
    return all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET])


def _get_drafts_in(folder: str, prefix: str = "TWITTER_") -> list[dict]:
    target = VAULT_PATH / folder
    if not target.exists():
        return []
    results = []
    for f in sorted(target.iterdir()):
        if f.suffix != ".md" or not f.name.upper().startswith(prefix):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        status = "unknown"
        cycle = "unknown"
        m = re.search(r"^status:\s*(.+)$", text, re.MULTILINE)
        if m:
            status = m.group(1).strip()
        m2 = re.search(r"^cycle_type:\s*(.+)$", text, re.MULTILINE)
        if m2:
            cycle = m2.group(1).strip()
        results.append({"filename": f.name, "folder": folder, "status": status, "cycle": cycle})
    return results


MAX_TWEETS_PER_THREAD = 20  # safety cap — prevents runaway threads


def _extract_tweets(filepath: Path) -> list[str]:
    """Extract individual tweets from a thread draft."""
    text = filepath.read_text(encoding="utf-8")
    # Strip null bytes and non-printable control characters (prompt injection defence)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
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

    # Split on "---" separator or numbered tweet format (1/, 2/, etc.)
    if "---" in content:
        tweets = [t.strip() for t in content.split("---") if t.strip()]
    else:
        tweets = re.split(r"\n(?=\d+/)", content)
        tweets = [t.strip() for t in tweets if t.strip()]

    # Truncate each tweet to 280 chars and cap thread length
    return [t[:280] for t in tweets[:MAX_TWEETS_PER_THREAD]]


def _log_action(target: str, result: str, error: str = ""):
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
        "action_type": "twitter_mcp_post",
        "actor": "twitter_mcp_server",
        "target": target,
        "parameters": {"dry_run": DRY_RUN},
        "result": result,
        "error": error,
    })
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


@mcp.tool(structured_output=False)
def list_twitter_drafts(folder: str = "all") -> str:
    """
    List Twitter drafts in the vault.

    Args:
        folder: Which folder to check. Options: "needs_action", "approved", "completed", "all".
                Defaults to "all".
    """
    folder_map = {
        "needs_action": ["Needs_Action"],
        "approved": ["Approved"],
        "completed": ["Completed"],
        "all": ["Needs_Action", "Approved", "Completed"],
    }
    folders = folder_map.get(folder.lower(), folder_map["all"])
    all_drafts = []
    for f in folders:
        all_drafts.extend(_get_drafts_in(f))

    if not all_drafts:
        return f"No Twitter drafts found in: {', '.join(folders)}"

    lines = [f"Found {len(all_drafts)} Twitter draft(s):\n"]
    for d in all_drafts:
        lines.append(f"  [{d['folder']}] {d['filename']} | cycle: {d['cycle']} | status: {d['status']}")
    return "\n".join(lines)


@mcp.tool(structured_output=False)
def post_twitter_draft(filename: str) -> str:
    """
    Post a specific approved Twitter draft as a thread to Twitter/X.
    The file must be in /Vault/Approved/ and start with TWITTER_.
    Respects DRY_RUN setting.

    Args:
        filename: The .md filename in /Vault/Approved/ to post (e.g. TWITTER_20260324_123abc.md)
    """
    if not filename.upper().startswith("TWITTER_"):
        return f"Error: filename must start with TWITTER_. Got: {filename}"

    # Reject path traversal attempts — filename must be a bare name only
    if filename != Path(filename).name or ".." in filename or "/" in filename or "\\" in filename:
        return f"Error: Invalid filename (path traversal not allowed): {filename}"

    approved_dir = VAULT_PATH / "Approved"
    filepath = (approved_dir / filename).resolve()
    if not str(filepath).startswith(str(approved_dir.resolve())):
        return f"Error: File path escapes Approved directory: {filename}"
    if not filepath.exists():
        return f"Error: File not found in /Vault/Approved/: {filename}"

    tweets = _extract_tweets(filepath)
    if not tweets:
        return f"Error: Could not extract tweet content from {filename}"

    if DRY_RUN:
        _log_action(filename, "dry_run")
        preview = "\n".join([f"  Tweet {i+1}: {t[:80]}..." for i, t in enumerate(tweets)])
        return (
            f"[DRY RUN] Would post {len(tweets)}-tweet thread to Twitter.\n"
            f"File: {filename}\n"
            f"Thread preview:\n{preview}\n"
            "Set DRY_RUN=false in .env for live posting."
        )

    if not _credentials_configured():
        return (
            "Error: Twitter credentials not configured. "
            "Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, "
            "TWITTER_ACCESS_TOKEN_SECRET in .env\n"
            "Get credentials from: developer.twitter.com"
        )

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )

        tweet_ids = []
        reply_to_id = None
        for tweet_text in tweets:
            if reply_to_id:
                response = client.create_tweet(text=tweet_text, in_reply_to_tweet_id=reply_to_id)
            else:
                response = client.create_tweet(text=tweet_text)
            tweet_id = response.data["id"]
            tweet_ids.append(tweet_id)
            reply_to_id = tweet_id

        # Move to Completed
        completed_dir = VAULT_PATH / "Completed"
        completed_dir.mkdir(exist_ok=True)
        dest = completed_dir / filename
        file_content = filepath.read_text(encoding="utf-8")
        file_content = re.sub(r"^(status:\s*).*$", r"\1posted", file_content, count=1, flags=re.MULTILINE)
        file_content += (
            f"\n\n## Post Result\n"
            f"- **Tweet IDs:** {', '.join(tweet_ids)}\n"
            f"- **Thread Length:** {len(tweets)} tweets\n"
            f"- **Posted At:** {datetime.now().isoformat()}\n"
        )
        dest.write_text(file_content, encoding="utf-8")
        filepath.unlink()

        _log_action(filename, "success")
        return (
            f"Posted {len(tweets)}-tweet thread to Twitter successfully.\n"
            f"First Tweet ID: {tweet_ids[0]}\n"
            f"File archived to /Completed/{filename}"
        )

    except ImportError:
        return "Error: tweepy not installed. Run: pip install tweepy"
    except Exception as e:
        _log_action(filename, "failure", str(e))
        return f"Failed to post: {e}"


@mcp.tool(structured_output=False)
def get_timeline_summary(limit: int = 5) -> str:
    """
    Fetch a summary of recent tweets from the authenticated Twitter account (read-only).

    Args:
        limit: Number of recent tweets to retrieve (default: 5, max: 20).
    """
    if not _credentials_configured():
        return (
            "Error: Twitter credentials not configured. "
            "Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, "
            "TWITTER_ACCESS_TOKEN_SECRET in .env"
        )

    limit = min(max(1, limit), 20)

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )

        # Get authenticated user's ID
        me = client.get_me()
        user_id = me.data.id

        tweets = client.get_users_tweets(
            id=user_id,
            max_results=limit,
            tweet_fields=["created_at", "public_metrics"],
        )

        if not tweets.data:
            return "No recent tweets found."

        lines = [f"Recent {len(tweets.data)} tweet(s):\n"]
        for i, tweet in enumerate(tweets.data, 1):
            text_preview = tweet.text[:100]
            created = getattr(tweet, "created_at", "")
            metrics = getattr(tweet, "public_metrics", {}) or {}
            likes = metrics.get("like_count", 0)
            retweets = metrics.get("retweet_count", 0)
            lines.append(f"{i}. [{created}] {text_preview}... (likes: {likes}, RT: {retweets})")
        return "\n".join(lines)

    except ImportError:
        return "Error: tweepy not installed. Run: pip install tweepy"
    except Exception as e:
        return f"Failed to fetch timeline: {e}"


if __name__ == "__main__":
    mcp.run()
