# Skill: Post to Facebook

## Description
Post an approved Facebook draft to a Facebook Page via the Meta Graph API.
Reads from `/Vault/Approved/`, posts live, then archives to `/Vault/Completed/`.

## Status
GOLD TIER — Requires FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN in `.env`.
Set `DRY_RUN=false` and `AUTO_POST_FACEBOOK=true` for fully autonomous posting.

## Workflow

```
Vault/Needs_Action/FACEBOOK_*.md   (draft created by facebook_watcher.py)
        |
        v
AI fact-checks via GPT-4o
    Verified + auto_post_eligible: true  ->  auto-moved to /Approved/ (if AUTO_POST_FACEBOOK=true)
    Needs Review                         ->  stays in /Needs_Action/ for human action
        |
        v
facebook_post.py  ->  POST to Meta Graph API /{page_id}/feed
        |
        v
Vault/Completed/FACEBOOK_*.md  (status: posted, Facebook Post ID recorded)
```

## Instructions

When the user asks to "post to Facebook", "run Facebook post", or "check Facebook drafts":

1. **List drafts**: Call MCP tool `list_facebook_drafts` or check `Vault/Approved/` for `FACEBOOK_*.md` files
2. **Show content**: Display the draft content before posting (safety check)
3. **Verify credentials**: Confirm `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` are set in `.env`
4. **Post via MCP**: Use `post_facebook_draft(filename)` from the `gold-facebook` MCP server
   — OR run directly:
   ```bash
   cd "C:/Users/user/Gold Tier/Watchers"
   python facebook_post.py
   ```
5. **Report result**: Confirm post published, show Facebook Post ID, confirm file archived

## Auto-Post Mode (Gold Tier)

Set in `.env` to enable fully autonomous posting of verified drafts:
```
AUTO_POST_FACEBOOK=true
DRY_RUN=false
```

When `AUTO_POST_FACEBOOK=true`, verified drafts with `auto_post_eligible: true` in their
frontmatter are automatically moved from `/Needs_Action/` to `/Approved/` and posted without
human intervention.

## DRY_RUN Behavior
- `DRY_RUN=true` — logs intent only, no API call made, no file moved
- `DRY_RUN=false` — live post to Facebook Page

## Credentials Needed (in .env)
```
FB_PAGE_ID=your_page_id_here
FB_PAGE_ACCESS_TOKEN=your_long_lived_page_access_token_here
AUTO_POST_FACEBOOK=false
```
Get credentials from: Meta for Developers -> Your App -> Graph API Explorer
Required permissions: `pages_manage_posts`, `pages_read_engagement`

## MCP Server
Server name: `gold-facebook`
Script: `Watchers/facebook_mcp_server.py`
Tools:
  - `list_facebook_drafts(folder?)` — list drafts by folder
  - `post_facebook_draft(filename)` — post a specific approved draft
  - `get_page_summary(limit?)` — fetch recent posts from the page

## Important Rules
- Never post without a draft in `/Vault/Approved/` (unless AUTO_POST_FACEBOOK=true for verified drafts)
- Never expose FB_PAGE_ACCESS_TOKEN in output — treat it as a secret
- Always log every post attempt to `/Vault/Logs/YYYY-MM-DD.json`
- On failure, leave draft in `/Vault/Approved/` — do not delete
- Rotate FB_PAGE_ACCESS_TOKEN every 60 days or immediately if exposed
