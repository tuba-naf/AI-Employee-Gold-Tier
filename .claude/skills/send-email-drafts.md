# Skill: Send Email Drafts

## Description
Email all pending content drafts to the human reviewer. Collects drafts from `/Vault/Needs_Action/` that have not yet been emailed, builds an HTML digest, and delivers it via SMTP to REVIEWER_EMAIL.

## Instructions

When the user asks to "send drafts", "email drafts", or "deliver drafts", follow these steps:

1. **Check pending drafts**: Use the `list_pending_drafts` MCP tool (silver-email server) to see what drafts are waiting
2. **Confirm before sending**: Tell the user how many drafts will be sent and which platforms
3. **Send via MCP tool**: Use `send_draft_email` MCP tool to trigger delivery
   - Default: all platforms (linkedin, instagram, news)
   - Or pass specific platforms if user requests (e.g. `platforms: ["linkedin"]`)
4. **Report result**: Confirm email was sent, which drafts were marked as "emailed", and the recipient address

## MCP Tools Used
- `list_pending_drafts(platforms?)` — list drafts not yet emailed
- `send_draft_email(platforms?)` — send HTML digest email to REVIEWER_EMAIL

## Alternative (direct script)
If MCP tools are unavailable, run via Bash:
```bash
cd C:/Users/user/Silver-Tier/Watchers
python email_drafts.py --platform linkedin instagram news
```

## Important Rules
- Never send if `DRY_RUN=true` in `.env` — log only
- Never expose SMTP credentials in output
- Log every send action to `/Vault/Logs/YYYY-MM-DD.json`
- Drafts marked "emailed" in frontmatter are skipped automatically

## Expected Output
- Confirmation of email sent to reviewer
- Count of drafts included
- Platforms covered
- Any drafts skipped (already emailed or no pending)
