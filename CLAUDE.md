# CLAUDE.md — Gold Tier AI Employee

## Project Overview
Personal AI Employee (Digital FTE) — **Gold Tier**.
- **Brain:** Claude Code (you)
- **Memory/GUI:** Obsidian Vault at `C:/Users/user/Gold Tier/Vault`
- **Senses:** Python Watchers (LinkedIn, Instagram, News, Facebook, Twitter, Filesystem)
- **Delivery:** Auto-post to Facebook/Instagram/Twitter (Graph API / Twitter API v2) | Email via SMTP for LinkedIn/News

## Vault Path
```
C:/Users/user/Gold Tier/Vault
```

## Watchers Path
```
C:/Users/user/Gold Tier/Watchers
```

## Gold Tier Capabilities
| Capability | Status | Notes |
|---|---|---|
| Content drafting | Active | LinkedIn, Instagram, News, Facebook, Twitter |
| AI fact-checking | Active | Via OpenAI GPT-4o |
| Facebook auto-posting | Active | Via Meta Graph API (set AUTO_POST_FACEBOOK=true) |
| Instagram auto-posting | Active | Via Meta Graph API two-step (set AUTO_POST_INSTAGRAM=true) |
| Twitter auto-posting | Active | Via Twitter API v2 / tweepy (set AUTO_POST_TWITTER=true) |
| Email draft delivery | Active | LinkedIn/News drafts emailed for review |
| HITL approval workflow | Active | Human reviews email, posts manually (LinkedIn/News) |
| Scheduling | Active | Windows Task Scheduler via .bat files |
| Ralph Wiggum loop | Active | Stop hook for autonomous multi-step task completion |
| Weekly Content Briefing | Active | weekly_audit.py — post counts + Facebook engagement report |
| Odoo content tracking | Active | gold-odoo MCP — tracks posts/drafts/engagement in Odoo Projects |
| Email MCP server | Active | gold-email — email tools callable by Claude Code |
| Facebook MCP server | Active | gold-facebook — Facebook post/list/summary tools |
| Twitter MCP server | Active | gold-twitter — Twitter draft list/post/timeline tools |
| Odoo MCP server | Active | gold-odoo — content strategy tracking in Odoo |

## MCP Servers
| Server Name | Script | Tools |
|---|---|---|
| `gold-email` | `Watchers/email_mcp_server.py` | `list_pending_drafts`, `send_draft_email` |
| `gold-facebook` | `Watchers/facebook_mcp_server.py` | `list_facebook_drafts`, `post_facebook_draft`, `get_page_summary` |
| `gold-twitter` | `Watchers/twitter_mcp_server.py` | `list_twitter_drafts`, `post_twitter_draft`, `get_timeline_summary` |
| `gold-odoo` | `Watchers/odoo_mcp_server.py` | `log_published_post`, `create_content_task`, `update_post_engagement`, `get_content_summary`, `get_weekly_content_report` |

### MCP Tool Reference
**gold-email:**
- **`list_pending_drafts(platforms?)`** — List pending drafts not yet emailed. Platforms: linkedin, instagram, news, facebook
- **`send_draft_email(platforms?)`** — Send HTML digest email to reviewer. Respects DRY_RUN setting.

**gold-facebook:**
- **`list_facebook_drafts(folder?)`** — List Facebook drafts by folder: needs_action, approved, completed, all
- **`post_facebook_draft(filename)`** — Post a specific approved Facebook draft to the Page
- **`get_page_summary(limit?)`** — Fetch recent posts from the Facebook Page (read-only)

**gold-twitter:**
- **`list_twitter_drafts(folder?)`** — List Twitter drafts by folder: needs_action, approved, completed, all
- **`post_twitter_draft(filename)`** — Post a specific approved Twitter draft as a thread to Twitter/X
- **`get_timeline_summary(limit?)`** — Fetch recent tweets from the authenticated account (read-only)

## Folder Structure
```
Vault/
├── Inbox/              # Raw task drops
├── Needs_Action/       # Drafts pending verification
├── Plans/              # AI-generated task plans
├── Completed/          # Verified and approved/posted content
├── Pending_Approval/   # Actions awaiting human sign-off
├── Approved/           # Human-approved or auto-approved, ready to post
├── Rejected/           # Rejected actions (archived, never retried)
├── Logs/               # JSON audit logs (immutable, 90-day retention)
├── Dashboard.md        # Live status dashboard
└── Company_Handbook.md # Rules of engagement

Watchers/               # Python watcher/posting scripts (outside Vault)
├── base_watcher.py
├── linkedin_watcher.py
├── instagram_watcher.py
├── news_watcher.py
├── facebook_watcher.py       # Gold Tier — RSS watcher for Facebook drafts
├── twitter_watcher.py        # Gold Tier — RSS watcher for Twitter/X drafts
├── email_drafts.py
├── filesystem_watcher.py
├── facebook_post.py          # Gold Tier — Meta Graph API auto-poster
├── instagram_post.py         # Gold Tier — Meta Graph API two-step poster
├── twitter_post.py           # Gold Tier — Twitter API v2 thread poster
├── linkedin_post.py
├── email_mcp_server.py
├── facebook_mcp_server.py    # Gold Tier — MCP server (gold-facebook)
├── twitter_mcp_server.py     # Gold Tier — MCP server (gold-twitter)
├── ralph_wiggum_hook.py      # Gold Tier — Stop hook for Ralph Wiggum loop
├── orchestrator.py           # Gold Tier — Ralph loop task launcher
├── weekly_audit.py           # Gold Tier — CEO Briefing generator
├── scheduled_run.py
├── run_all_watchers.py
├── run_social.bat
├── run_news.bat
├── run_facebook.bat          # Gold Tier — Facebook draft + post scheduler
├── run_twitter.bat           # Gold Tier — Twitter draft + post scheduler
├── run_weekly_audit.bat      # Gold Tier — Monday CEO briefing scheduler
└── run_filesystem_watcher.bat
```

## Available Skills
| Skill File | Invoke With | Purpose |
|---|---|---|
| `generate-content.md` | "generate a post for [platform]" | Create a draft following rotation cycle |
| `verify-content.md` | "verify [filename]" | Fact-check a draft in /Needs_Action/ |
| `review-drafts.md` | "review drafts" | Summarize all pending drafts |
| `update-dashboard.md` | "update dashboard" | Refresh Dashboard.md |
| `process-inbox.md` | "process inbox" | Convert /Inbox/ files to structured drafts |
| `send-email-drafts.md` | "send drafts" | Email pending drafts to reviewer |
| `post-to-linkedin.md` | "post to LinkedIn" | Post approved LinkedIn draft via API |
| `post-to-facebook.md` | "post to Facebook" | Post approved Facebook draft via Meta Graph API |
| `post-to-instagram.md` | "post to Instagram" | Post approved Instagram draft via Meta Graph API |
| `post-to-twitter.md` | "post to Twitter" | Post approved Twitter draft as a thread via Twitter API v2 |
| `generate-ceo-briefing.md` | "generate briefing" / "weekly briefing" / "how did content perform" | Run weekly audit + Facebook engagement report |
| `odoo-content.md` | "log post to Odoo" / "show content summary" / "update engagement" | Track content strategy in Odoo Projects |
| `ralph-loop.md` | "/ralph-loop" | Start autonomous multi-step loop via Stop hook |

## Content Workflow

### Facebook (Auto-Post — Gold Tier)
```
facebook_watcher.py → RSS feed → FACEBOOK_*.md in /Inbox/
         |
         v
AI fact-checks draft (GPT-4o)
    Verified + auto_post_eligible: true → /Needs_Action/ + /Completed/ (archive)
    Needs Review → /Needs_Action/ with flags
         |
         v
facebook_post.py (scheduled via run_facebook.bat)
    AUTO_POST_FACEBOOK=true  → auto-moves verified drafts to /Approved/ → posts to Facebook Page
    AUTO_POST_FACEBOOK=false → waits for human to move file to /Approved/
         |
         v
/Completed/FACEBOOK_*.md (status: posted, Facebook Post ID recorded)
```

### Twitter/X (Auto-Post — Gold Tier)
```
twitter_watcher.py → RSS feed → TWITTER_*.md in /Inbox/
         |
         v
AI fact-checks draft (GPT-4o)
    Verified + auto_post_eligible: true → /Needs_Action/ + /Completed/ (archive)
    Needs Review → /Needs_Action/ with flags
         |
         v
twitter_post.py (scheduled via run_twitter.bat)
    AUTO_POST_TWITTER=true  → auto-moves verified drafts to /Approved/ → posts thread to Twitter/X
    AUTO_POST_TWITTER=false → waits for human to move file to /Approved/
         |
         v
/Completed/TWITTER_*.md (status: posted, Tweet IDs recorded)
```

### LinkedIn / News (HITL — Silver Tier behaviour)
```
Watcher → draft in /Needs_Action/ → AI verify → email_drafts.py sends digest
         |
         v
Reviewer reads email → copy-pastes approved content manually
```

## Ralph Wiggum Loop
The Stop hook in `.claude/settings.json` calls `ralph_wiggum_hook.py` every time Claude tries to exit.

- If no active task state: Claude exits normally (no impact)
- If active task (`/Vault/In_Progress/.ralph_state.json` exists with `status: active`):
  - Task NOT done + iterations remaining → hook blocks exit and re-injects task prompt
  - Task done OR max iterations reached → hook allows exit

To start a loop: `python orchestrator.py start --task <name> --prompt "<task>" --max-iterations 10`
To cancel: `python orchestrator.py reset`
To check: `python orchestrator.py status`

## Security Rules — NON-NEGOTIABLE
1. **Never commit `.env`** — it contains live API keys and access tokens
2. **Never log or output credential values** — mask FB_PAGE_ACCESS_TOKEN in any response
3. **Never delete** files from `/Completed/` or `/Logs/` — immutable audit trail
4. **Always check** `DRY_RUN` — if `true`, log intended actions only, never execute
5. **Never post** Facebook content with `DRY_RUN=true`
6. **Rotate credentials** immediately if any key appears in a log or conversation
7. **Always verify** facts before marking a draft as verified or auto_post_eligible

## Environment Variables
Config: `C:/Users/user/Gold Tier/.env`
Template: `C:/Users/user/Gold Tier/.env.example`

Key variables:
- `VAULT_PATH` — `C:/Users/user/Gold Tier/Vault`
- `TIER` — `gold`
- `DRY_RUN` — `true` during testing, `false` for live posting
- `OPENAI_API_KEY` — for content generation and fact-checking
- `SMTP_HOST/PORT/USER/PASSWORD` — Gmail SMTP config
- `REVIEWER_EMAIL` — where LinkedIn/Instagram/News draft emails are delivered
- `FB_PAGE_ID` — Facebook Page ID for auto-posting
- `FB_PAGE_ACCESS_TOKEN` — Long-lived Page Access Token (rotate every 60 days)
- `AUTO_POST_FACEBOOK` — `true` to auto-post verified drafts; `false` for HITL
- `IG_USER_ID` — Instagram Business User ID for auto-posting
- `IG_PAGE_ACCESS_TOKEN` — Same token as FB if accounts are linked
- `IG_DEFAULT_IMAGE_URL` — Public HTTPS image URL required by Instagram Graph API
- `AUTO_POST_INSTAGRAM` — `true` to auto-post verified Instagram drafts
- `TWITTER_API_KEY` — Twitter/X API Key (Consumer Key)
- `TWITTER_API_SECRET` — Twitter/X API Key Secret
- `TWITTER_ACCESS_TOKEN` — Twitter/X Access Token (requires Read+Write app permissions)
- `TWITTER_ACCESS_TOKEN_SECRET` — Twitter/X Access Token Secret
- `TWITTER_BEARER_TOKEN` — Twitter/X Bearer Token (for read operations)
- `AUTO_POST_TWITTER` — `true` to auto-post verified Twitter drafts
- `TWITTER_CHECK_INTERVAL` — watcher polling interval in seconds (default: 14400)
- `MAX_DRAFTS_PER_RUN` — safety cap per scheduled run (default: 1 per platform)
- `FACEBOOK_CHECK_INTERVAL` — watcher polling interval in seconds (default: 14400)

## Content Rules (Summary)
- Topics: Climate, Sustainability, Environment — Pakistan-focused
- Cycle: Local Problem → Local Hopeful → Global Problem → Global Hopeful
- LinkedIn: 500+ words | Instagram: 300+ words | News: 600+ words | Facebook: 400+ words | Twitter: 280 chars/tweet (3-5 tweets)
- Recency: last 7-14 days only
- All statistics must be cited inline: [1], [2], etc.
- No fabricated or unverifiable numbers — flag for human review if uncertain

See `Vault/Company_Handbook.md` for full content rules.
