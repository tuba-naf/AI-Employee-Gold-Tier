# Skill: Post to Instagram

## Description
Post an approved Instagram draft to an Instagram Business Account via the Meta Graph API.
Uses the two-step Graph API flow: create media container → publish.
Reads from `/Vault/Approved/`, posts live, archives to `/Vault/Completed/`.

## Status
GOLD TIER — Requires IG_USER_ID, IG_PAGE_ACCESS_TOKEN, and IG_DEFAULT_IMAGE_URL in `.env`.
Instagram Business Account must be linked to a Facebook Page.

## API Flow (Meta Graph API)
```
Step 1: POST /{ig-user-id}/media
        Params: image_url=<public_url>, caption=<content>, access_token=<token>
        Returns: container_id

Step 2: POST /{ig-user-id}/media_publish
        Params: creation_id=<container_id>, access_token=<token>
        Returns: post_id (ig_media_id)
```

## Workflow
```
Vault/Needs_Action/INSTA_*.md   (draft created by instagram_watcher.py)
        |
        v
AI fact-checks via GPT-4o
    Verified + auto_post_eligible: true → auto-moved to /Approved/ (if AUTO_POST_INSTAGRAM=true)
    Needs Review → stays in /Needs_Action/ for human action
        |
        v
instagram_post.py → Meta Graph API two-step publish
        |
        v
Vault/Completed/INSTA_*.md  (status: posted, Instagram Post ID recorded)
```

## Instructions

When the user asks to "post to Instagram" or "run Instagram post":

1. **List approved drafts**: Check `Vault/Approved/` for `INSTA_*.md` files
2. **Show content**: Display caption before posting
3. **Verify credentials**: Confirm IG_USER_ID, IG_PAGE_ACCESS_TOKEN, IG_DEFAULT_IMAGE_URL in `.env`
4. **Run script**:
   ```bash
   cd "C:/Users/user/Gold Tier/Watchers"
   python instagram_post.py
   ```
5. **Report result**: Confirm post published, show Instagram Post ID

## Auto-Post Mode (Gold Tier)
```
AUTO_POST_INSTAGRAM=true
DRY_RUN=false
```
Verified drafts with `auto_post_eligible: true` auto-post without manual approval.

## Image Requirement
Instagram requires an image for all posts. Set `IG_DEFAULT_IMAGE_URL` to a publicly
accessible HTTPS image URL (e.g., your website's default banner or a CDN-hosted image).

## DRY_RUN Behavior
- `DRY_RUN=true` — logs intent only, no API calls made
- `DRY_RUN=false` — live post to Instagram

## Credentials Needed (in .env)
```
IG_USER_ID=your_instagram_business_user_id
IG_PAGE_ACCESS_TOKEN=your_long_lived_page_access_token
IG_DEFAULT_IMAGE_URL=https://your-site.com/images/default_post.jpg
AUTO_POST_INSTAGRAM=false
```

Get credentials:
1. Link Instagram Business Account to a Facebook Page
2. Meta for Developers → Create App → Add Instagram Graph API product
3. Generate a long-lived Page Access Token (valid ~60 days)
4. Get IG User ID: GET /me?fields=id,username&access_token=<token> on the linked IG account

## Important Rules
- Never post without content in `/Vault/Approved/` (unless AUTO_POST_INSTAGRAM=true for verified)
- Never expose IG_PAGE_ACCESS_TOKEN in output
- Always log every post attempt to `/Vault/Logs/YYYY-MM-DD.json`
- On failure, leave draft in `/Vault/Approved/` — do not delete
- Rotate IG_PAGE_ACCESS_TOKEN every 60 days or immediately if exposed
- Instagram requires a public image URL — posts without IG_DEFAULT_IMAGE_URL will be skipped
