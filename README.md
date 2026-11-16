# FLEX Portal Bot

A small Python bot that checks my university portal (FLEX, FAST NUCES) for new marks and attendance, and sends a notification to my phone only when something changes.

## What it does

- Reads attendance and marks for my enrolled courses
- Compares them with the previous check
- Sends a notification through ntfy only when something is new
- Shows each update with the course name and every figure under its portal label (obtained marks, total marks, class average, and so on)
- Notifies me when I need to log in again

## About the portal's human check

The bot does not solve or bypass the portal's "are you a robot?" check. It runs in my own Chrome, where the check usually passes on its own. If it does not, I log in myself. It only reads my own data, as I would manually.

## Files

- flex_check.py: reads attendance and marks, compares, and sends the notification
- auto_login.py: clicks Sign In when the login page is showing and the browser has already filled it in
- test_notify.py: sends a test message to check that notifications work
- fake_change.py: edits the bot's saved copy so it reports a pretend change (for demos only)

## Setup

1. Install Python, Google Chrome, and the ntfy app on your phone.
2. Install Playwright:

        pip install playwright

3. Open Chrome with a separate profile and a debugging port:

        chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\flex_chrome"

4. Log in to the portal in that window.
5. In flex_check.py, set `topic` to your own long, random ntfy topic name, and set the course codes to yours.
6. Run:

        python flex_check.py

## Privacy

Never upload your browser profile folder, your saved marks files, or your ntfy topic name. Anyone who knows the topic name can read your notifications.

## Note

This is a personal learning project. Check your university's rules about automated tools before using it on its portal.