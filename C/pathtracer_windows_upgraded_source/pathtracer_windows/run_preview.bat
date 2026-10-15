@echo off
setlocal
echo Rendering preview...
pathtracer.exe --scene showcase --width 640 --height 360 --spp 16 --depth 8 --output preview.bmp
if errorlevel 1 (
  echo Render failed.
  exit /b 1
)
echo Saved preview.bmp
endlocal
