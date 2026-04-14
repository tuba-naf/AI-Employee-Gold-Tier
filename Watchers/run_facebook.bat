@echo off
REM Gold Tier AI Employee — Facebook Draft Generation + Auto-Post
REM Schedule with Windows Task Scheduler (recommended: every 12 hours)
REM
REM Task Scheduler setup:
REM   Program/script: C:\Users\user\Gold Tier\Watchers\run_facebook.bat
REM   Start in: C:\Users\user\Gold Tier\Watchers

cd /d "C:\Users\user\Gold Tier\Watchers"

echo [%date% %time%] Starting Facebook watcher run...

REM Step 1: Generate a new Facebook draft from RSS feeds
python scheduled_run.py --platform facebook

REM Step 2: Auto-post any approved drafts to Facebook Page
python facebook_post.py

echo [%date% %time%] Facebook run complete.
