@echo off
REM Windows launcher for the game client.
cd /d "%~dp0"
python client\client.py %*
pause
