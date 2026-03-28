@echo off
echo Starting Chrome, AI mode...
start chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_ai_temp"

echo Waiting for Chrome...
timeout /t 3

echo Starting assistent...
call venv\Scripts\activate.bat
python main.py
pause