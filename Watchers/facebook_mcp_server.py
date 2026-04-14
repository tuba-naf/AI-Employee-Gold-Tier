"""
Facebook MCP Server — Gold Tier AI Employee
Exposes Facebook draft management and posting as MCP tools callable by Claude Code.

Tools:
  - list_facebook_drafts   : List pending/approved Facebook drafts in the vault
  - post_facebook_draft    : Post a specific approved draft to the Facebook Page
  - get_page_summary       : Fetch recent posts from the Facebook Page (read-only)
"""

import os
import sys
import json
import re
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from mcp.server.fastmcp import FastMCP

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
GRAPH_API_URL = "https://graph.facebook.com/v19.0"

mcp = FastMCP("Gold Tier Facebook MCP")


def _get_drafts_in(folder: str, prefix: str = "FACEBOOK_") -> list[dict]:
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


MAX_CONTENT_LENGTH = 5000  # chars — prevents prompt injection flooding


def _extract_content(filepath: Path) -> str:
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
    return content[:MAX_CONTENT_LENGTH]


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
        "action_type": "facebook_mcp_post",
        "actor": "facebook_mcp_server",
        "target": target,
        "parameters": {"dry_run": DRY_RUN},
        "result": result,
        "error": error,
    })
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


@mcp.tool(structured_output=False)
def list_facebook_drafts(folder: str = "all") -> str:
    """
    List Facebook drafts in the vault.

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
        return f"No Facebook drafts found in: {', '.join(folders)}"

    lines = [f"Found {len(all_drafts)} Facebook draft(s):\n"]
    for d in all_drafts:
        lines.append(f"  [{d['folder']}] {d['filename']} | cycle: {d['cycle']} | status: {d['status']}")
    return "\n".join(lines)


@mcp.tool(structured_output=False)
def post_facebook_draft(filename: str) -> str:
    """
    Post a specific approved Facebook draft to the Facebook Page.
    The file must be in /Vault/Approved/ and start with FACEBOOK_.
    Respects DRY_RUN setting.

    Args:
        filename: The .md filename in /Vault/Approved/ to post (e.g. FACEBOOK_20260324_123abc.md)
    """
    if not filename.upper().startswith("FACEBOOK_"):
        return f"Error: filename must start with FACEBOOK_. Got: {filename}"

    # Reject path traversal attempts — filename must be a bare name only
    if filename != Path(filename).name or ".." in filename or "/" in filename or "\\" in filename:
        return f"Error: Invalid filename (path traversal not allowed): {filename}"

    approved_dir = VAULT_PATH / "Approved"
    filepath = (approved_dir / filename).resolve()
    if not str(filepath).startswith(str(approved_dir.resolve())):
        return f"Error: File path escapes Approved directory: {filename}"
    if not filepath.exists():
        return f"Error: File not found in /Vault/Approved/: {filename}"

    content = _extract_content(filepath)
    if not content:
        return f"Error: Could not extract content from {filename}"

    if DRY_RUN:
        _log_action(filename, "dry_run")
        return (
            f"[DRY RUN] Would post to Facebook Page {FB_PAGE_ID or '<not set>'}.\n"
            f"File: {filename}\n"
            f"Content preview: {content[:200]}...\n"
            "Set DRY_RUN=false in .env for live posting."
        )

    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        return (
            "Error: Facebook credentials not configured. "
            "Set FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN in .env"
        )

    try:
        url = f"{GRAPH_API_URL}/{FB_PAGE_ID}/feed"
        payload = {"message": content, "access_token": FB_PAGE_ACCESS_TOKEN}
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        post_id = result.get("id", "")

        # Move to Completed
        completed_dir = VAULT_PATH / "Completed"
        completed_dir.mkdir(exist_ok=True)
        dest = completed_dir / filename
        file_content = filepath.read_text(encoding="utf-8")
        file_content = re.sub(r"^(status:\s*).*$", r"\1posted", file_content, count=1, flags=re.MULTILINE)
        file_content += f"\n\n## Post Result\n- **Facebook Post ID:** {post_id}\n- **Posted At:** {datetime.now().isoformat()}\n"
        dest.write_text(file_content, encoding="utf-8")
        filepath.unlink()

        _log_action(filename, "success")
        return f"Posted to Facebook successfully.\nPost ID: {post_id}\nFile archived to /Completed/{filename}"

    except requests.HTTPError as e:
        _log_action(filename, "api_error", str(e))
        return f"Facebook API error: {e}"
    except Exception as e:
        _log_action(filename, "failure", str(e))
        return f"Failed to post: {e}"


@mcp.tool(structured_output=False)
def get_page_summary(limit: int = 5) -> str:
    """
    Fetch a summary of the most recent posts from the Facebook Page (read-only).

    Args:
        limit: Number of recent posts to retrieve (default: 5, max: 25).
    """
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        return (
            "Error: Facebook credentials not configured. "
            "Set FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN in .env"
        )

    limit = min(max(1, limit), 25)

    try:
        url = f"{GRAPH_API_URL}/{FB_PAGE_ID}/feed"
        params = {
            "fields": "id,message,created_time,permalink_url",
            "limit": limit,
            "access_token": FB_PAGE_ACCESS_TOKEN,
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        posts = data.get("data", [])

        if not posts:
            return "No posts found on the Facebook Page."

        lines = [f"Recent {len(posts)} post(s) from Facebook Page {FB_PAGE_ID}:\n"]
        for i, post in enumerate(posts, 1):
            msg = (post.get("message") or "")[:100]
            created = post.get("created_time", "")
            pid = post.get("id", "")
            lines.append(f"{i}. [{created}] {msg}... (id: {pid})")
        return "\n".join(lines)

    except requests.HTTPError as e:
        return f"Facebook API error: {e}"
    except Exception as e:
        return f"Failed to fetch page summary: {e}"


if __name__ == "__main__":
    mcp.run()
