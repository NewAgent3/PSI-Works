@echo off
REM One-time setup for Windows
cd /d "%~dp0"
echo Installing dependencies (ursina + panda3d)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Done. Now run launch_server.bat (in one window) and launch_client.bat (in another).
pause
