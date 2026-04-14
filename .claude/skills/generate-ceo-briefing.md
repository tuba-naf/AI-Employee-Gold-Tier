# Skill: Generate Content Briefing

## Description
Generate the weekly Monday Morning Content Briefing. Reads audit logs, completed content
counts, backlog, and live Facebook engagement stats via the Graph API to produce a
structured `/Vault/Briefings/YYYY-MM-DD_Content_Briefing.md`.

## Trigger
Invoke when user says "generate briefing", "weekly briefing", "Monday briefing",
or "how did content perform this week".

## What the Briefing Contains
| Section | Source |
|---------|--------|
| Content output per platform | /Vault/Completed/ file counts |
| Backlog | /Vault/Needs_Action/ file counts |
| Content cycle status | Watcher state files (.facebook_state.json etc.) |
| Facebook engagement | Meta Graph API — likes, comments, shares, reach per post |
| Best performing post | Highest reach/likes post from the past 7 days |
| Errors & failures | /Vault/Logs/YYYY-MM-DD.json entries |
| Suggestions | Rule-based analysis (backlog size, errors, missing posts) |

## Instructions

When the user asks for a briefing:

1. **Run the audit script**:
   ```bash
   cd "C:/Users/user/Gold Tier/Watchers"
   python weekly_audit.py
   ```
2. **Read the output**: `Vault/Briefings/YYYY-MM-DD_Content_Briefing.md`
3. **Present key highlights** to the user:
   - How many posts were published per platform
   - Facebook engagement summary (best post, total likes/comments)
   - Any errors or backlog items needing attention

## Facebook Engagement Requirements
- `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` must be set in `.env`
- Token needs `pages_read_engagement` permission for reach stats
- Without credentials, engagement section shows a config reminder

## Schedule via Task Scheduler (Every Monday 8:00 AM)
Use `run_weekly_audit.bat`:
```
Trigger: Weekly, Monday, 08:00 AM
Action: C:\Users\user\Gold Tier\Watchers\run_weekly_audit.bat
```

## Output Location
`Vault/Briefings/YYYY-MM-DD_Content_Briefing.md`

## Important Rules
- The briefing is read-only — it never modifies vault content
- Briefing files are stored permanently in /Briefings/ (audit trail)
- Facebook API calls are read-only — no posts are created or modified
