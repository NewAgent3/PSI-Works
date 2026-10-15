@echo off
setlocal
echo Building patched pathtracer.exe (custom scene support)...
gcc -O3 -std=c99 -ffast-math -static -s -o pathtracer.exe pathtracer.c -lm
if errorlevel 1 (
  echo Build failed. Make sure MinGW-w64 gcc is on PATH.
  exit /b 1
)
echo Built pathtracer.exe
endlocal
