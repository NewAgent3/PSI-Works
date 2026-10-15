==============================================================
  PathTracer++ for Windows (self-contained source package)
==============================================================

WHAT IS INCLUDED
  pathtracer.c        - Upgraded single-file path tracer source
  pathtracer.exe      - Prebuilt Windows x64 executable
  build_mingw.bat     - Rebuild with MinGW-w64
  build_msvc.bat      - Rebuild with Microsoft Visual C++
  run_preview.bat     - Fast preview render
  run_final.bat       - Higher-quality final render
  sample_render.bmp   - Example image rendered by the source

NO EXTRA LIBRARIES REQUIRED
  - No SDL, OpenGL, DirectX, stb, or external image libraries
  - Source is self-contained in one C file
  - Output is BMP or PPM

MAJOR UPGRADES OVER THE ORIGINAL
  - Multithreaded tiled rendering on Windows
  - Better default quality and more flexible command line
  - Multiple built-in scenes:
      showcase
      cornell
      random
      glass
  - ACES-style tone mapping + gamma correction
  - Deterministic seed support for reproducible renders
  - Backward compatibility with old usage: pathtracer.exe 128
  - BMP and PPM output support
  - Cleaner project packaging with ready-to-use scripts

QUICK START
  1) Double-click run_preview.bat for a fast test render
  2) Double-click run_final.bat for a better-quality render
  3) Or use the executable from CMD / PowerShell:

       pathtracer.exe
       pathtracer.exe 256
       pathtracer.exe --scene cornell --width 1024 --height 1024 --spp 512 --output cornell.bmp
       pathtracer.exe --scene random --width 1280 --height 720 --spp 128 --threads 0 --output random.bmp

COMMAND LINE OPTIONS
  --width N        image width
  --height N       image height
  --spp N          samples per pixel
  --depth N        maximum path depth
  --threads N      number of worker threads (0 = auto detect)
  --scene NAME     showcase | cornell | random | glass
  --vfov X         vertical field of view
  --aperture X     thin lens aperture
  --focus X        explicit focus distance
  --seed N         deterministic random seed
  --output FILE    output file (.bmp or .ppm)
  --quiet          suppress progress output
  --help           show help

REBUILDING FROM SOURCE
  Option A - MinGW-w64
    Double-click build_mingw.bat

    Equivalent command:
      gcc -O3 -std=c99 -ffast-math -static -s -o pathtracer.exe pathtracer.c -lm

  Option B - MSVC (Developer Command Prompt)
    Double-click build_msvc.bat

    Equivalent command:
      cl /O2 /MT pathtracer.c

DEFAULTS
  Resolution : 960x540
  Samples    : 128 spp
  Depth      : 12
  Scene      : showcase
  Output     : output.bmp

SUGGESTED SETTINGS
  Fast preview:
    --width 640 --height 360 --spp 16

  Good balance:
    --width 1280 --height 720 --spp 128

  Final quality:
    --width 1920 --height 1080 --spp 256 or higher

NOTES
  - Higher spp reduces noise but increases render time
  - The random scene contains many spheres and benefits from more samples
  - Cornell works best with square output sizes like 1024x1024
  - The executable is prebuilt, but full source is included for modification
