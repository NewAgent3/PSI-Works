@echo off
setlocal
echo Building PathTracer++ with MinGW-w64...
gcc -O3 -std=c99 -ffast-math -static -s -o pathtracer.exe pathtracer.c -lm
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)
echo Build complete: pathtracer.exe
endlocal
