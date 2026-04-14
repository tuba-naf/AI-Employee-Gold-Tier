@echo off
cd /d "C:\Users\user\Silver-Tier\Watchers"
"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" scheduled_run.py --platform linkedin instagram news
"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" email_drafts.py --platform linkedin instagram news
