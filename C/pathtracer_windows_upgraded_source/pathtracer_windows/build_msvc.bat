@echo off
setlocal
echo Building PathTracer++ with MSVC...
cl /O2 /MT pathtracer.c
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)
echo Build complete: pathtracer.exe
endlocal
