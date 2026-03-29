#!/bin/zsh

echo "[1/3] Starting Chrome in Debug Mode..."
# Note: On Mac, we use the full path to the Chrome binary
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome_ai_temp" &

# Give Chrome a few seconds to open the debugging port
echo "[2/3] Waiting for Chrome..."
sleep 3

# --- THE MAC VENV ACTIVATION ---
echo "[3/3] Activating environment and starting Assistant..."
source venv/bin/activate

# Start your Python script
python3 main.py