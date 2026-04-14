# Skill: Update Dashboard

## Description
Scan the vault folders and update `/Vault/Dashboard.md` with current counts of pending drafts, verified content, and recent activity.

## Instructions

When asked to update the dashboard:

1. **Count drafts in `/Vault/Needs_Action/`** by platform:
   - Files starting with `LINKEDIN_` → LinkedIn count
   - Files starting with `INSTA_` → Instagram count
   - Files starting with `NEWS_` → News count
2. **Count completed items in `/Vault/Completed/`** by platform
3. **Check recent log entries** in `/Vault/Logs/` for latest activity
4. **Determine current cycle position** by checking the watcher state files in `/Vault/Watchers/`
5. **Write the updated Dashboard.md** with:
   - System status
   - Draft counts table (Pending | Verified | Total)
   - Content rotation status
   - Recent activity (last 5 actions from logs)
   - Folder quick links

### Dashboard Template
```markdown
---
last_updated: [current date/time]
auto_refresh: true
---

# AI Employee Dashboard — Silver Tier

## System Status
- **Mode:** Email Delivery (Draft → Verify → Email → Human Posts)
- **Tier:** Silver
- **Watchers:** LinkedIn | Instagram | News | Filesystem

## Pending Content Drafts
| Platform   | Pending | Verified | Total |
|------------|---------|----------|-------|
| LinkedIn   | [n]     | [n]      | [n]   |
| Instagram  | [n]     | [n]      | [n]   |
| News       | [n]     | [n]      | [n]   |

## Content Rotation Status
- **Current Cycle Position:** [position]
- **Cycle:** Local Problem → Local Hopeful → Global Problem → Global Hopeful

## Recent Activity
- [timestamp] [action description]
...
```
