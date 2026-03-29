#!/bin/zsh

export GOOGLE_APPLICATION_CREDENTIALS="/Users/nemanjaudovic/PycharmProjects/pola_bajta/pola-bajta/your_existing_key.json"

echo "[1/3] Starting Chrome on Google..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome_ai_temp" \
  "https://www.google.com" &

while ! nc -z localhost 9222; do
  sleep 0.5
done

echo "✅ Chrome Debugger is UP and on Google.com"

echo "[2/3] Activating venv..."
source venv/bin/activate

echo "[3/3] Starting Assistant..."
python3 main.py