# Skill: Post to LinkedIn

## Description
Post an approved LinkedIn draft to LinkedIn. Reads from `/Vault/Approved/`, posts via LinkedIn API, then archives to `/Vault/Completed/`.

## Status
STRUCTURE READY — LinkedIn API credentials not yet configured.
To activate: set `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_AUTHOR_URN` in `.env`.

## Workflow

```
Vault/Needs_Action/LINKEDIN_*.md   (draft created by watcher)
        |
        v
email_drafts.py  →  email sent to reviewer
        |
        v
Human approves  →  manually moves file to Vault/Approved/
        |
        v
linkedin_post.py  →  POST to LinkedIn API
        |
        v
Vault/Completed/LINKEDIN_*.md  (status: posted, archived)
```

## Instructions

When the user asks to "post to LinkedIn" or "run LinkedIn post":

1. **Check approved drafts**: List files in `Vault/Approved/` starting with `LINKEDIN_`
2. **Confirm content**: Show the user the draft content before posting
3. **Check credentials**: Verify `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_AUTHOR_URN` are set in `.env`
4. **Run script**:
   ```bash
   cd C:/Users/user/Silver-Tier/Watchers
   python linkedin_post.py
   ```
5. **Report result**: Confirm post published and file moved to `/Completed/`

## DRY_RUN Behavior
- `DRY_RUN=true` — logs intent only, no actual post, no file moved
- `DRY_RUN=false` — live post to LinkedIn

## Credentials Needed (in .env)
```
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_AUTHOR_URN=urn:li:person:your_person_id
```
Get these from: https://www.linkedin.com/developers/apps

## Important Rules
- Never post without human approval (file must be in `/Vault/Approved/`)
- Never expose credentials in output
- Always log every post attempt to `/Vault/Logs/YYYY-MM-DD.json`
- On failure, leave draft in `/Vault/Approved/` — do not delete
