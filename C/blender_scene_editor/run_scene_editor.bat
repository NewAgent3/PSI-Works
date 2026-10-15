@echo off
REM Launch the Blender-style 3D Scene Editor for PathTracer++
cd /d "%~dp0"
python scene_editor.py
if errorlevel 1 (
    echo.
    echo Python launch failed. Make sure Python 3.8+ is installed and on PATH.
    pause
)
