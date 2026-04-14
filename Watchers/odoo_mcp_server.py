"""
Odoo Content Strategy MCP Server — Gold Tier AI Employee
Tracks content strategy, published posts, and engagement inside Odoo Community.
Uses Odoo's Project module (tasks = content pieces) via JSON-RPC API (Odoo 19+).

This is NOT an accounting integration — it is a content management integration.
Each platform is an Odoo Project. Each post/draft is an Odoo Task.

Tools:
  - log_published_post     : Record a published post in Odoo (platform, title, cycle, status)
  - get_content_summary    : Get content performance summary from Odoo (posts per platform, cycle)
  - create_content_task    : Create a content task in Odoo for a draft
  - update_post_engagement : Store Facebook/Instagram engagement data on an Odoo task
  - get_weekly_content_report : Pull this week's content stats from Odoo for the briefing

Odoo Setup Required:
  1. Install Odoo Community 19+
  2. Install the "Project" module in Odoo
  3. Create 4 projects manually: LinkedIn, Facebook, Instagram, News
  4. Generate an API Key: Settings > Technical > API Keys
  5. Add credentials to .env

Environment variables:
  ODOO_URL      — http://localhost:8069
  ODOO_DB       — your database name
  ODOO_USERNAME — your login email
  ODOO_API_KEY  — generated API key
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from mcp.server.fastmcp import FastMCP

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "")
ODOO_API_KEY = os.getenv("ODOO_API_KEY", "")
ODOO_API_KEY_ROTATED = os.getenv("ODOO_API_KEY_ROTATED", "")  # date last rotated: YYYY-MM-DD
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
MAX_SUMMARY_DAYS = 365  # cap for get_content_summary days parameter
VALID_PLATFORMS = set(["linkedin", "facebook", "instagram", "news", "twitter"])

# Warn if Odoo API key is overdue for rotation (90-day policy)
if ODOO_API_KEY and ODOO_API_KEY_ROTATED:
    try:
        rotated_date = datetime.strptime(ODOO_API_KEY_ROTATED, "%Y-%m-%d")
        age_days = (datetime.now() - rotated_date).days
        if age_days > 90:
            import sys as _sys
            print(
                f"[gold-odoo WARNING] Odoo API key is {age_days} days old (last rotated {ODOO_API_KEY_ROTATED}). "
                "Rotate it in Odoo: Settings > Technical > API Keys. Update ODOO_API_KEY_ROTATED in .env.",
                file=_sys.stderr,
            )
    except ValueError:
        pass

mcp = FastMCP("Gold Tier Odoo Content MCP")

# Maps platform names to Odoo project names
PLATFORM_PROJECTS = {
    "linkedin": "LinkedIn Content",
    "facebook": "Facebook Content",
    "instagram": "Instagram Content",
    "news": "News Content",
    "twitter": "Twitter Content",
}

# Content cycle stage names (must match Odoo task stages)
CYCLE_TAGS = {
    "local_problem": "Local Problem",
    "local_hopeful": "Local Hopeful",
    "global_problem": "Global Problem",
    "global_hopeful": "Global Hopeful",
}


class OdooClient:
    """Thin Odoo JSON-RPC client."""

    def __init__(self):
        self.url = ODOO_URL.rstrip("/")
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.api_key = ODOO_API_KEY
        self._uid = None

    def _check_config(self):
        if not self.db or not self.username or not self.api_key:
            raise ValueError(
                "Odoo not configured. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY in .env"
            )

    def _rpc(self, model: str, method: str, args: list, kwargs: dict = None) -> object:
        self._check_config()
        if not self._uid:
            auth = self._post("/web/dataset/call_kw", {
                "model": "res.users", "method": "authenticate",
                "args": [self.db, self.username, self.api_key, {}], "kwargs": {},
            })
            if not auth:
                raise PermissionError("Odoo authentication failed. Check credentials.")
            self._uid = auth

        return self._post("/web/dataset/call_kw", {
            "model": model, "method": method,
            "args": args, "kwargs": kwargs or {},
        })

    def _post(self, endpoint: str, params: dict) -> object:
        resp = requests.post(
            f"{self.url}{endpoint}",
            json={"jsonrpc": "2.0", "method": "call", "id": 1, "params": params},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Odoo error: {data['error'].get('data', {}).get('message', data['error'])}")
        return data.get("result")

    def search_read(self, model: str, domain: list, fields: list, limit: int = 100) -> list:
        return self._rpc(model, "search_read", [domain, fields], {"limit": limit})

    def create(self, model: str, vals: dict) -> int:
        return self._rpc(model, "create", [vals])

    def write(self, model: str, ids: list, vals: dict) -> bool:
        return self._rpc(model, "write", [ids, vals])


odoo = OdooClient()


def _get_or_create_project(platform: str) -> int | None:
    """Get Odoo project ID for a platform, creating it if it doesn't exist."""
    project_name = PLATFORM_PROJECTS.get(platform.lower(), f"{platform.title()} Content")
    projects = odoo.search_read("project.project", [("name", "=", project_name)], ["id", "name"])
    if projects:
        return projects[0]["id"]
    # Create the project
    project_id = odoo.create("project.project", {
        "name": project_name,
        "description": f"Content tracking for {platform.title()} platform — Gold Tier AI Employee",
    })
    return project_id


def _get_or_create_tag(tag_name: str) -> int | None:
    """Get or create a task tag in Odoo."""
    tags = odoo.search_read("project.tags", [("name", "=", tag_name)], ["id"])
    if tags:
        return tags[0]["id"]
    return odoo.create("project.tags", {"name": tag_name})


@mcp.tool(structured_output=False)
def log_published_post(platform: str, title: str, cycle_type: str, filename: str = "") -> str:
    """
    Record a published post in Odoo as a completed task.
    Call this after a post is successfully published to any platform.

    Args:
        platform:   Platform name — linkedin, facebook, instagram, news, twitter
        title:      Post title or first 100 chars of content
        cycle_type: Content cycle — local_problem, local_hopeful, global_problem, global_hopeful
        filename:   The .md filename from /Vault/Completed/ (optional)
    """
    if platform.lower() not in VALID_PLATFORMS:
        return f"Error: Invalid platform '{platform}'. Valid options: {sorted(VALID_PLATFORMS)}"

    if not ODOO_DB:
        return "Error: Odoo not configured. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY in .env"

    if DRY_RUN:
        return (
            f"[DRY RUN] Would log to Odoo:\n"
            f"  Platform: {platform}\n"
            f"  Title: {title[:80]}\n"
            f"  Cycle: {cycle_type}\n"
            f"  File: {filename}\n"
            "Set DRY_RUN=false in .env to log in Odoo."
        )

    try:
        project_id = _get_or_create_project(platform)
        cycle_label = CYCLE_TAGS.get(cycle_type, cycle_type.replace("_", " ").title())
        tag_id = _get_or_create_tag(cycle_label)

        task_vals = {
            "name": title[:250],
            "project_id": project_id,
            "description": f"Published by Gold Tier AI Employee\nFile: {filename}\nCycle: {cycle_label}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "tag_ids": [(4, tag_id)] if tag_id else [],
            "date_deadline": datetime.now().strftime("%Y-%m-%d"),
            "stage_id": _get_done_stage_id(project_id),
        }
        task_id = odoo.create("project.task", task_vals)
        return (
            f"Logged to Odoo successfully.\n"
            f"  Task ID: {task_id}\n"
            f"  Project: {PLATFORM_PROJECTS.get(platform.lower(), platform)}\n"
            f"  Cycle tag: {cycle_label}"
        )
    except ValueError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Odoo error: {e}"


def _get_done_stage_id(project_id: int) -> int | None:
    """Get or create a 'Published' stage for the project."""
    stages = odoo.search_read(
        "project.task.type",
        [("name", "in", ["Published", "Done", "Posted"])],
        ["id", "name"],
        limit=1,
    )
    if stages:
        return stages[0]["id"]
    return odoo.create("project.task.type", {
        "name": "Published",
        "project_ids": [(4, project_id)],
    })


@mcp.tool(structured_output=False)
def create_content_task(platform: str, title: str, cycle_type: str, draft_file: str = "") -> str:
    """
    Create a content task in Odoo when a new draft is created.
    Represents a draft moving through the content pipeline.

    Args:
        platform:   Platform name — linkedin, facebook, instagram, news, twitter
        title:      Draft title or topic
        cycle_type: Content cycle — local_problem, local_hopeful, global_problem, global_hopeful
        draft_file: The .md filename in /Vault/Needs_Action/ (optional)
    """
    if platform.lower() not in VALID_PLATFORMS:
        return f"Error: Invalid platform '{platform}'. Valid options: {sorted(VALID_PLATFORMS)}"

    if not ODOO_DB:
        return "Error: Odoo not configured."

    if DRY_RUN:
        return (
            f"[DRY RUN] Would create Odoo task:\n"
            f"  Platform: {platform} | Cycle: {cycle_type}\n"
            f"  Title: {title[:80]}\n"
            "Set DRY_RUN=false to create in Odoo."
        )

    try:
        project_id = _get_or_create_project(platform)
        cycle_label = CYCLE_TAGS.get(cycle_type, cycle_type.replace("_", " ").title())
        tag_id = _get_or_create_tag(cycle_label)

        task_id = odoo.create("project.task", {
            "name": title[:250],
            "project_id": project_id,
            "description": f"Draft created by Gold Tier AI Employee\nFile: {draft_file}\nCycle: {cycle_label}",
            "tag_ids": [(4, tag_id)] if tag_id else [],
        })
        return f"Content task created in Odoo. Task ID: {task_id} | Project: {PLATFORM_PROJECTS.get(platform.lower(), platform)}"
    except Exception as e:
        return f"Odoo error: {e}"


@mcp.tool(structured_output=False)
def update_post_engagement(task_id: int, likes: int, comments: int, shares: int, reach: int = 0) -> str:
    """
    Store Facebook/Instagram engagement data on an existing Odoo task.
    Call this after fetching engagement stats from the Graph API.

    Args:
        task_id:  Odoo Task ID (returned by log_published_post)
        likes:    Number of likes
        comments: Number of comments
        shares:   Number of shares
        reach:    Reach/impressions (optional)
    """
    if not ODOO_DB:
        return "Error: Odoo not configured."

    if DRY_RUN:
        return f"[DRY RUN] Would update task {task_id}: likes={likes}, comments={comments}, shares={shares}, reach={reach}"

    try:
        engagement_note = (
            f"\n\n--- Engagement Stats ({datetime.now().strftime('%Y-%m-%d')}) ---\n"
            f"Likes: {likes} | Comments: {comments} | Shares: {shares}"
            + (f" | Reach: {reach:,}" if reach else "")
        )
        tasks = odoo.search_read("project.task", [("id", "=", task_id)], ["description"])
        if not tasks:
            return f"Task {task_id} not found in Odoo."
        current_desc = tasks[0].get("description") or ""
        odoo.write("project.task", [task_id], {"description": current_desc + engagement_note})
        return f"Engagement updated on task {task_id}: likes={likes}, comments={comments}, shares={shares}"
    except Exception as e:
        return f"Odoo error: {e}"


@mcp.tool(structured_output=False)
def get_content_summary(days: int = 7) -> str:
    """
    Get a content performance summary from Odoo for the past N days.
    Shows published posts per platform and cycle type distribution.

    Args:
        days: Number of past days to include (default: 7)
    """
    if not ODOO_DB:
        return "Error: Odoo not configured. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY in .env"

    days = min(max(1, days), MAX_SUMMARY_DAYS)

    try:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        lines = [f"Content Summary — Last {days} days (from {since})\n"]
        total = 0

        for platform_key, project_name in PLATFORM_PROJECTS.items():
            projects = odoo.search_read(
                "project.project", [("name", "=", project_name)], ["id"]
            )
            if not projects:
                lines.append(f"  {project_name}: No Odoo project found")
                continue

            project_id = projects[0]["id"]
            tasks = odoo.search_read(
                "project.task",
                [("project_id", "=", project_id), ("write_date", ">=", since)],
                ["name", "tag_ids", "stage_id"],
            )
            count = len(tasks)
            total += count
            lines.append(f"  {project_name}: {count} post(s)")

        lines.append(f"\n  Total posts tracked: {total}")
        return "\n".join(lines)

    except ValueError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Odoo error: {e}"


@mcp.tool(structured_output=False)
def get_weekly_content_report() -> str:
    """
    Pull this week's content stats from Odoo for the Monday Content Briefing.
    Returns a formatted summary of posts per platform and cycle distribution.
    """
    return get_content_summary(days=7)


if __name__ == "__main__":
    mcp.run()
