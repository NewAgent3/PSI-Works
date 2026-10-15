@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scene_maker.py
) else (
  python scene_maker.py
)
endlocal
