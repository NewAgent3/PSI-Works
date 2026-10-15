==============================================================
  Scene Maker for PathTracer++
==============================================================

WHAT THIS IS
  A visual scene editor (Python + Tkinter, no extra deps) that
  lets you place spheres, lights and the camera on a top-down
  grid, then click RENDER to invoke pathtracer.exe.

WHAT IS INCLUDED
  scene_maker.py        - The GUI scene maker
  pathtracer.c          - PATCHED pathtracer source with custom
                          scene file support (drop-in replacement
                          for the original pathtracer.c)
  build_mingw.bat       - Build pathtracer.exe with MinGW-w64
  build_msvc.bat        - Build pathtracer.exe with MSVC
  run_scene_maker.bat   - Launch the GUI
  example.scene         - Example .scene text file
  README.txt            - This file

ONE-TIME SETUP
  1) Build the patched pathtracer.exe in this folder:
        Double-click build_mingw.bat   (needs MinGW-w64 gcc)
        or build_msvc.bat              (needs MSVC dev prompt)
     Or copy your existing pathtracer.exe here and rebuild it
     from the included pathtracer.c (the patch adds two CLI
     flags: --scene custom and --scenefile <path>).

  2) Make sure Python 3.8+ is installed (standard library only,
     Tkinter is included by default on Windows).

QUICK START
  1) Double-click run_scene_maker.bat
  2) Edit scene in the GUI:
       - Left mouse: select / drag sphere on XZ plane
       - Right mouse: add new sphere at click location
       - Toolbar:   Add Sphere / Light / Glass, Delete, Duplicate
       - Right panel: edit name, material, X/Y/Z, radius,
                      RGB color, fuzz (metal), IR (dielectric)
       - Camera & sky: look from / look at, FoV, aperture, focus
       - Render: width, height, spp, depth, threads, seed,
                 output file, exe path
  3) Pick a quality preset (Preview / Balanced / Final) or set
     values manually, then click the big blue RENDER button.
  4) The image opens automatically when the render finishes.

SAVE / LOAD
  File > Save / Save as...   - writes scene to JSON
  File > Open...             - loads a previously saved scene
  Every render also writes a current.scene (text format) next
  to pathtracer.exe for transparency / debugging.

.scene FILE FORMAT
  See example.scene for the full reference. It is plain text,
  line-based, with one statement per line. You can hand-edit
  these files and run them directly:

     pathtracer.exe --scene custom --scenefile my.scene ^
                    --width 1280 --height 720 --spp 256 ^
                    --output my.bmp

COMPATIBILITY
  The patched pathtracer.exe still supports every original
  scene and option:
      pathtracer.exe --scene showcase ...
      pathtracer.exe --scene cornell ...
      pathtracer.exe --scene random ...
      pathtracer.exe --scene glass ...
  It just adds:
      --scene custom --scenefile <path>

MATERIALS
  lambert     diffuse, parameters: r g b
  metal       reflective, parameters: r g b fuzz
              (fuzz 0=mirror, 1=very rough)
  dielectric  glass, parameter: ir (1.0=air, 1.33=water, 1.5=glass, 2.4=diamond)
              For a hollow glass ball, add a second dielectric
              sphere with a NEGATIVE radius at the same center.
  light       emissive, parameters: r g b   (values > 1 are HDR)

COORDINATE SYSTEM
  X right, Y up, Z toward viewer. The top-down canvas shows
  the XZ plane (Y = height is edited in the side panel).
  The ground in the default scene is a huge sphere centered
  at (0, -1000, 0) with radius 1000 - leave it as-is unless
  you want a different ground material.

TROUBLESHOOTING
  - "Pathtracer executable not found": set the correct path in
    the 'Pathtracer exe' field (or place pathtracer.exe next
    to scene_maker.py).
  - "unknown option --scenefile" or scene comes out as showcase:
    your pathtracer.exe is the ORIGINAL unpatched one. Rebuild
    using the pathtracer.c shipped here.
  - Render looks black: check that you added at least one
    sphere with material 'light', or the sky is not 'black'.
  - Render is grainy: increase spp (samples per pixel).
