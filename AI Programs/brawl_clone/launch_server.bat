@echo off
REM Windows launcher for the dedicated server
cd /d "%~dp0"
echo Starting Brawl Clone server on port 5555...
echo Other players connect with their LAN IP or use 127.0.0.1 locally.
python server\server.py --host 0.0.0.0 --port 5555 %*
pause
