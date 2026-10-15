==============================================================
  Pure-C Path Tracer for Windows (x86_64)
==============================================================

FILES
  pathtracer.exe     - Windows 64-bit executable (statically linked, no DLLs needed)
  pathtracer.c       - Single-file C source (no external libraries)
  sample_render.bmp  - Sample render output (640x480, 64 samples/pixel)

USAGE
  Double-click pathtracer.exe, or from CMD/PowerShell:

      pathtracer.exe             (defaults to 64 samples per pixel)
      pathtracer.exe 128         (use 128 samples per pixel - higher quality)
      pathtracer.exe 16          (use 16 samples per pixel - faster preview)

  It writes "output.bmp" into the current directory.

REBUILDING FROM SOURCE (optional)
  With MinGW-w64 on Windows:
      gcc -O3 -ffast-math -o pathtracer.exe pathtracer.c -lm

  With MSVC (Developer Command Prompt):
      cl /O2 pathtracer.c

FEATURES
  - Monte Carlo path tracing
  - Lambertian (diffuse), Metal (with fuzz), Dielectric (glass) materials
  - Hollow glass sphere (negative-radius trick)
  - Emissive light source
  - Depth-of-field (thin-lens camera with aperture)
  - Antialiasing via stochastic sub-pixel sampling
  - Gamma 2.0 output, BMP 24-bit writer (no external image libs)
  - Pure ANSI C, only <stdio.h>, <stdlib.h>, <stdint.h>, <string.h>,
    <math.h>, <time.h> from the standard library

RENDER TIME (approx., single threaded)
   16 spp : ~1-2 seconds
   64 spp : ~5-10 seconds
  256 spp : ~20-40 seconds
