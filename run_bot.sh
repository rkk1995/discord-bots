#!/bin/bash

# Discord Bot Auto-Restart Script
# This script ensures the Discord bot is always running

# Change to the script's directory
cd "$(dirname "$0")"

BOT_SCRIPT="bot.py"
PYTHON_CMD="python3"
LOG_FILE="bot.log"

# Check if bot is running (more specific pattern)
if pgrep -fx ".*python3.*bot.py.*" > /dev/null
then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Discord bot is running." >> "$LOG_FILE"
else 
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Discord bot is not running, starting bot..." >> "$LOG_FILE"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Start the bot in background (let Python handle its own logging)
    nohup $PYTHON_CMD $BOT_SCRIPT > /dev/null 2>&1 &
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Discord bot started." >> "$LOG_FILE"
fi
exit 0 