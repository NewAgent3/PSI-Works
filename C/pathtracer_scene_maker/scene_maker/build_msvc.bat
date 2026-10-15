@echo off
setlocal
echo Building patched pathtracer.exe (custom scene support, MSVC)...
cl /O2 /MT pathtracer.c
if errorlevel 1 (
  echo Build failed. Run from a Developer Command Prompt for VS.
  exit /b 1
)
echo Built pathtracer.exe
endlocal
