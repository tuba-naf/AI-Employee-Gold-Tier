"""
Email MCP Server — Silver Tier AI Employee
Exposes email draft delivery as MCP tools callable by Claude Code.

Tools:
  - list_pending_drafts   : List drafts in /Needs_Action/ not yet emailed
  - send_draft_email      : Send HTML digest email to reviewer inbox
"""

import os
import sys

# Ensure Watchers/ is on the path so we can import email_drafts
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from mcp.server.fastmcp import FastMCP
from email_drafts import (
    get_pending_drafts,
    get_verified_count,
    build_email,
    send_email,
    mark_drafts_as_emailed,
    log_email_action,
    REVIEWER_EMAIL,
    DRY_RUN,
)

VAULT_PATH = os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault")
VALID_PLATFORMS = ["linkedin", "instagram", "news", "facebook"]

mcp = FastMCP("Gold Tier Email MCP")


@mcp.tool(structured_output=False)
def list_pending_drafts(platforms: list[str] = None) -> str:
    """
    List all pending content drafts in the vault that have not been emailed yet.

    Args:
        platforms: List of platforms to check. Options: linkedin, instagram, news.
                   Defaults to all platforms.
    """
    if platforms is None:
        platforms = VALID_PLATFORMS

    invalid = [p for p in platforms if p not in VALID_PLATFORMS]
    if invalid:
        return f"Invalid platform(s): {invalid}. Valid options: {VALID_PLATFORMS}"

    drafts = get_pending_drafts(VAULT_PATH, platforms)
    if not drafts:
        return "No pending drafts found."

    lines = [f"Found {len(drafts)} pending draft(s):\n"]
    for d in drafts:
        lines.append(
            f"  [{d['platform']}] {d['filename']}"
            f" | cycle: {d['cycle_type']}"
            f" | status: {d['status']}"
        )
    return "\n".join(lines)


@mcp.tool(structured_output=False)
def send_draft_email(platforms: list[str] = None) -> str:
    """
    Send pending content drafts to the reviewer email inbox as a formatted HTML digest.
    Drafts are marked as 'emailed' after successful delivery (live mode only).

    Args:
        platforms: List of platforms to include. Options: linkedin, instagram, news.
                   Defaults to all platforms.
    """
    if platforms is None:
        platforms = VALID_PLATFORMS

    invalid = [p for p in platforms if p not in VALID_PLATFORMS]
    if invalid:
        return f"Invalid platform(s): {invalid}. Valid options: {VALID_PLATFORMS}"

    drafts = get_pending_drafts(VAULT_PATH, platforms)
    if not drafts:
        return "No pending drafts found. No email sent."

    verified_count = get_verified_count(VAULT_PATH, platforms)
    msg = build_email(drafts, platforms, verified_count)
    success = send_email(msg)
    log_email_action(VAULT_PATH, platforms, len(drafts), success)

    if not success:
        return "Failed to send email. Check SMTP credentials in .env."

    if DRY_RUN:
        return (
            f"[DRY RUN] Would send email to {REVIEWER_EMAIL} "
            f"with {len(drafts)} draft(s) for {', '.join(platforms)}. "
            "Set DRY_RUN=false in .env for live delivery."
        )

    mark_drafts_as_emailed(drafts)
    return (
        f"Email sent to {REVIEWER_EMAIL} with {len(drafts)} draft(s) "
        f"({', '.join(platforms)}). Drafts marked as emailed."
    )


if __name__ == "__main__":
    mcp.run()
