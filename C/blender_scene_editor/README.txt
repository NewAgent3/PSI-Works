==============================================================
  PathTracer++ Scene Editor — Blender-style 3D
==============================================================

WHAT THIS IS
  A Blender-inspired 3D scene editor (Python + Tkinter, zero
  third-party dependencies) for the PathTracer++ renderer.
  This is a drop-in replacement for the old top-down Scene Maker
  — it reads and writes the exact same .scene file format and
  invokes the same patched pathtracer.exe, but offers a real
  3D editing experience.

KEY UPGRADES OVER THE ORIGINAL SCENE MAKER
  * Real perspective 3D viewport (software-rasterized — no GPU,
    no extra deps) with orbit / pan / zoom navigation.
  * Quad-view layout: large User Perspective + Top / Front / Side
    orthographic mini-views, always in sync.
  * Transform gizmos: drag X/Y/Z axis handles on the selected
    object in the viewport, plus a uniform-scale handle.
  * Object picking by clicking directly in any viewport (with
    correct depth ordering).
  * Blender-style dark theme and shortcuts (Numpad 1/3/7, etc.).
  * Outliner with material-color-coded entries and type icons.
  * Tabbed Properties Editor (Object / Material / World /
    Render) with a color swatch and one-click material presets
    (Gold, Chrome, Copper, Glass, Diamond, Warm/Cool Light…).
  * "Align Camera to Viewport" button — frame your shot in the
    editor camera, then snap the scene camera to that pose.
  * Backwards-compatible JSON save/load and .scene import/export.

WHAT'S INCLUDED
  scene_editor.py       - The new 3D scene editor (main app)
  pathtracer.c          - Patched pathtracer source (unchanged
                          from the original distribution — drop
                          in replacement for the original .c)
  build_mingw.bat       - Build pathtracer.exe with MinGW-w64
  build_msvc.bat        - Build pathtracer.exe with MSVC
  run_scene_editor.bat  - Launch the editor on Windows
  example.scene         - Example .scene text file
  README.txt            - This file

ONE-TIME SETUP
  1) Build the patched pathtracer.exe in this folder:
        Double-click build_mingw.bat  (needs MinGW-w64 gcc)
        or build_msvc.bat             (needs MSVC dev prompt)
     Or place an already-built patched pathtracer.exe in this
     folder.

  2) Make sure Python 3.8+ is installed (Tkinter ships with the
     standard Python installer on Windows).

LAUNCH
  Double-click run_scene_editor.bat
  or run:   python scene_editor.py

VIEWPORT NAVIGATION (Blender-style)
  MMB drag                Orbit the view around the pivot
  Shift + MMB drag        Pan
  Mouse wheel             Zoom in / out
  RMB drag                Also orbits (for trackpads w/o MMB)
  Double-click on object  Frame that object
  LMB on axis handle      Move along that axis
  LMB on scale handle     Uniform scale (the white box)
  LMB on empty space      Deselect

VIEW SHORTCUTS
  Numpad 1                Front view
  Numpad 3                Right view
  Numpad 7                Top view
  Numpad 5                Toggle Perspective / Orthographic
  Numpad .                Frame the selected object
  Home                    Frame all objects

EDIT SHORTCUTS
  A                       Open Add menu at cursor
  X  or  Delete           Delete selected
  Shift + D               Duplicate selected
  Ctrl + N / O / S        New / Open / Save
  F12                     Render

PANELS
  Outliner          — Click an item to select it. Items are
                      colour-coded by material type. The huge
                      ground sphere is shown but not selectable
                      in the viewport.
  Object tab        — Name, X/Y/Z (with R/G/B-coloured labels
                      matching the gizmo axes), radius.
  Material tab      — Material type, RGB sliders, color swatch
                      (click to open colour picker), roughness
                      (metal), IOR (glass). Quick presets:
                      Red, Green, Blue, Gold, Chrome, Copper,
                      Glass, Diamond, Warm Light, Cool Light.
  World tab         — Camera position / target / FoV / aperture
                      / focus + sky background. "Align Camera
                      to Viewport" snaps the scene camera to
                      match your current editor view.
  Render tab        — Width, height, samples per pixel, max
                      depth, threads, seed, output path,
                      pathtracer.exe path. Includes quality
                      presets (Preview / Balanced / Final /
                      Ultra) and the large RENDER button.

SAVING & LOADING
  File > Save / Save As         Saves the scene as JSON
  File > Open…                  Loads a previously saved JSON
  File > Import .scene…         Loads the plain-text .scene
                                format used by the renderer
  File > Export .scene…         Writes a plain-text .scene file
  Every render also writes a current.scene next to pathtracer.exe
  for transparency and debugging.

.scene FILE FORMAT (unchanged)
  See example.scene for the full reference. Plain text,
  line-based, one statement per line.

  sky <blue|studio|black|sunset>
  camera lookfrom <x> <y> <z>
  camera lookat   <x> <y> <z>
  camera vup      <x> <y> <z>
  camera vfov     <deg>
  camera aperture <a>
  camera focus    <dist>     (0 = auto)
  sphere lambert    <x> <y> <z> <r> <cr> <cg> <cb>
  sphere metal      <x> <y> <z> <r> <cr> <cg> <cb> <fuzz>
  sphere dielectric <x> <y> <z> <r> <ir>
  sphere light      <x> <y> <z> <r> <er> <eg> <eb>

  Hand-edited files can be rendered directly:

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
     pathtracer.exe --scene custom --scenefile <path>

MATERIALS
  lambert     Diffuse.   Params: r g b
  metal       Reflective. Params: r g b fuzz
              (fuzz 0 = mirror, 1 = very rough)
  dielectric  Glass.     Param: ir
              (1.0 = air, 1.33 = water, 1.5 = glass, 2.4 = diamond)
              For a hollow glass ball, add a second dielectric
              sphere with a NEGATIVE radius at the same center.
  light       Emissive.  Params: r g b (values > 1 are HDR)

COORDINATE SYSTEM
  X right, Y up, Z toward viewer. The default ground sphere is
  centered at (0, -1000, 0) with radius 1000 — leave it as-is
  unless you want a different ground material.

TROUBLESHOOTING
  "Pathtracer executable not found"
      Set the correct path in Render > Pathtracer, or drop
      pathtracer.exe next to scene_editor.py.

  "unknown option --scenefile" / output is the showcase scene
      Your pathtracer.exe is the original unpatched one.
      Rebuild from the pathtracer.c shipped here.

  Viewport is empty / black
      Drag MMB to orbit, scroll to zoom. The default scene
      should be visible after the window has finished sizing.

  Render looks black
      Make sure you have at least one 'light' sphere in the
      scene, or that the sky is not set to 'black'.

  Render is grainy
      Increase samples per pixel (spp). Try the Balanced or
      Final preset in the Render tab.

  Numpad shortcuts don't work
      Click somewhere inside the viewport first to give it
      focus. If you don't have a numpad, use View > Front /
      Right / Top from the menu.
