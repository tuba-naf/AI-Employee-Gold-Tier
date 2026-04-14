@echo off
REM Gold Tier AI Employee — Weekly CEO Briefing Generator
REM Schedule with Windows Task Scheduler (recommended: Every Monday at 08:00 AM)
REM
REM Task Scheduler setup:
REM   Program/script: C:\Users\user\Gold Tier\Watchers\run_weekly_audit.bat
REM   Start in: C:\Users\user\Gold Tier\Watchers

cd /d "C:\Users\user\Gold Tier\Watchers"

echo [%date% %time%] Generating weekly CEO briefing...
python weekly_audit.py
echo [%date% %time%] CEO briefing complete. Check Vault/Briefings/ for output.
