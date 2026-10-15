@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
echo.
echo Installed Global Fan-Strike dependencies.
pause
