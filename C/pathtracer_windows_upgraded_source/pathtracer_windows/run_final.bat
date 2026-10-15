@echo off
setlocal
echo Rendering final-quality image...
pathtracer.exe --scene showcase --width 1280 --height 720 --spp 128 --depth 12 --output final.bmp
if errorlevel 1 (
  echo Render failed.
  exit /b 1
)
echo Saved final.bmp
endlocal
