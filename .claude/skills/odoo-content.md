# Skill: Odoo Content Strategy

## Description
Track your content strategy inside Odoo Community using the `gold-odoo` MCP server.
Each platform is an Odoo Project. Each post/draft is an Odoo Task.
This is NOT accounting — it is a content management and tracking system.

## What Odoo Tracks for You
| Item | Odoo Object |
|------|-------------|
| LinkedIn posts | Tasks in "LinkedIn Content" project |
| Facebook posts | Tasks in "Facebook Content" project |
| Instagram posts | Tasks in "Instagram Content" project |
| News articles | Tasks in "News Content" project |
| Twitter threads | Tasks in "Twitter Content" project |
| Content cycle | Task tags (Local Problem, Global Hopeful, etc.) |
| Engagement data | Task description (likes, comments, shares, reach) |

## MCP Server
Server name: `gold-odoo`
Script: `Watchers/odoo_mcp_server.py`

## Tools
| Tool | When to Use |
|------|-------------|
| `create_content_task(platform, title, cycle, file?)` | When a new draft is created |
| `log_published_post(platform, title, cycle, file?)` | When a post goes live |
| `update_post_engagement(task_id, likes, comments, shares, reach?)` | After fetching FB/IG stats |
| `get_content_summary(days?)` | To see posts published per platform |
| `get_weekly_content_report()` | For the Monday Content Briefing |

## Instructions

### "Log that a post was published"
Call `log_published_post(platform, title, cycle_type, filename)`

### "Show content performance this week"
Call `get_content_summary(days=7)` and present results per platform.

### "Track a new draft in Odoo"
Call `create_content_task(platform, title, cycle_type, draft_file)`

### "Update engagement for a Facebook post"
1. Get the Odoo Task ID from when you logged the post
2. Fetch engagement from `get_page_summary()` (gold-facebook MCP)
3. Call `update_post_engagement(task_id, likes, comments, shares, reach)`

### "Generate Monday briefing with Odoo data"
Call `get_weekly_content_report()` — include result in the Content Briefing alongside vault stats.

## Odoo Setup (One-Time)
1. Install Odoo Community 19+ locally
2. Install the **Project** module inside Odoo
3. Generate API key: Odoo → Settings → Technical → API Keys
4. Add to `.env`:
   ```
   ODOO_URL=http://localhost:8069
   ODOO_DB=your_db_name
   ODOO_USERNAME=admin@yourcompany.com
   ODOO_API_KEY=your_api_key
   ```
5. Odoo projects (LinkedIn Content, Facebook Content, etc.) are **auto-created** on first use

## Content Pipeline with Odoo
```
Watcher creates draft
       ↓
create_content_task() → logged in Odoo as "In Progress" task
       ↓
Post published (Facebook/Instagram/etc.)
       ↓
log_published_post() → task moved to "Published" stage in Odoo
       ↓
Facebook engagement fetched (weekly_audit.py)
       ↓
update_post_engagement() → engagement stored on Odoo task
       ↓
get_weekly_content_report() → included in Monday Content Briefing
```

## Important Rules
- DRY_RUN=true means all Odoo writes are simulated — nothing is created
- Never expose ODOO_API_KEY in output
- Odoo projects are auto-created — no manual setup needed beyond installing Project module
