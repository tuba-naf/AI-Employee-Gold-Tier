@echo off
REM Gold Tier AI Employee — Twitter Draft Generation + Auto-Post
REM Schedule with Windows Task Scheduler (recommended: every 12 hours)
REM
REM Task Scheduler setup:
REM   Program/script: C:\Users\user\Gold Tier\Watchers\run_twitter.bat
REM   Start in: C:\Users\user\Gold Tier\Watchers

cd /d "C:\Users\user\Gold Tier\Watchers"

echo [%date% %time%] Starting Twitter run...

REM Step 1: Generate a new Twitter draft from RSS feeds
python scheduled_run.py --platform twitter

REM Step 2: Auto-post any approved drafts to Twitter
python twitter_post.py

echo [%date% %time%] Twitter run complete.
