# Skill: Post to Twitter (X)

## Description
Post an approved Twitter draft as a thread to Twitter/X via Twitter API v2.
Reads from `/Vault/Approved/`, posts tweet thread, archives to `/Vault/Completed/`.

## Status
GOLD TIER — Structure ready. Requires Twitter API v2 credentials.
Get credentials from: developer.twitter.com (Free tier available)

## Thread Format
Drafts are written as numbered threads:
```
1/ Pakistan loses X% of its glaciers every year...

2/ The Indus River, which feeds 90% of Pakistan's agriculture...

3/ But there is hope. The Billion Tree Tsunami project...

4/ What can YOU do? Share this thread and tag your local representative.
#Pakistan #ClimateAction
```

## Workflow
```
Vault/Needs_Action/TWITTER_*.md   (draft created by twitter_watcher.py)
        |
        v
AI fact-checks via GPT-4o
    Verified → /Needs_Action/ + /Completed/ (archive)
    Needs Review → stays in /Needs_Action/
        |
        v
Human moves to /Approved/  (or AUTO_POST_TWITTER=true for auto)
        |
        v
twitter_post.py → Twitter API v2 → thread posted
        |
        v
Vault/Completed/TWITTER_*.md  (status: posted, Tweet IDs recorded)
```

## Instructions

When user says "post to Twitter" or "run Twitter post":

1. **Check approved drafts**: List `Vault/Approved/TWITTER_*.md` files
2. **Show thread content**: Display all tweets before posting
3. **Verify credentials**: Confirm all 4 Twitter keys are in `.env`
4. **Run script**:
   ```bash
   cd "C:/Users/user/Gold Tier/Watchers"
   python twitter_post.py
   ```
5. **Report result**: Show tweet IDs and confirm thread posted

## Credentials Needed (in .env)
```
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
AUTO_POST_TWITTER=false
```

## How to Get Twitter API Credentials
1. Go to developer.twitter.com
2. Sign in with your Twitter/X account
3. Click **Create Project** → give it a name
4. Create an App inside the project
5. Go to **Keys and Tokens** tab
6. Generate: API Key, API Secret, Access Token, Access Token Secret, Bearer Token
7. Set App Permissions to **Read and Write**

## Dependency
Requires tweepy library:
```bash
pip install tweepy
```

## DRY_RUN Behavior
- `DRY_RUN=true` — logs all tweets but posts nothing
- `DRY_RUN=false` — live post to Twitter

## Important Rules
- Never post without content in `/Vault/Approved/`
- Never expose Twitter credentials in output
- Always log every post attempt to `/Vault/Logs/YYYY-MM-DD.json`
- On failure, leave draft in `/Vault/Approved/` — do not delete
- Twitter Free tier allows 1,500 tweets/month — stay within limits
