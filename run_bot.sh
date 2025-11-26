#!/bin/bash

# Discord Bot Auto-Restart Script
# This script ensures the Discord bot is always running

# Change to the script's directory
cd "$(dirname "$0")" || exit

BOT_SCRIPT="bot.py"
LOG_FILE="bot.log"

# Check if bot is running
# We look for the python process running the bot script
if pgrep -f "bot.py" >/dev/null; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Discord bot is running." >>"$LOG_FILE"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Discord bot is not running, starting bot..." >>"$LOG_FILE"

  # Ensure dependencies are up to date using uv
  if command -v uv >/dev/null 2>&1; then
    # Sync dependencies (quietly)
    uv sync >/dev/null 2>&1

    # Start the bot in background using uv run
    nohup uv run $BOT_SCRIPT >/dev/null 2>&1 &

    echo "$(date '+%Y-%m-%d %H:%M:%S') - Discord bot started with uv." >>"$LOG_FILE"
  else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: 'uv' not found. Please install uv." >>"$LOG_FILE"
    exit 1
  fi
fi
exit 0

