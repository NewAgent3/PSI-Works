# Python NES Emulator

A working Nintendo Entertainment System emulator written from scratch in pure Python.

## Features

- **Full 6502 CPU** — passes `nestest.nes` with 0 errors (all 151 official + 105 unofficial opcodes)
- **Scanline-accurate PPU** — background tiles, sprites (8x8 and 8x16), palettes, scrolling, sprite-0 hit, sprite overflow
- **iNES ROM loader** with mappers 0 (NROM), 2 (UxROM), and 3 (CNROM) — covers ~40% of all NES games including *Super Mario Bros.*, *Donkey Kong*, *Contra*, *Mega Man*, *Castlevania*, *Duck Hunt*, etc.
- **Controller input** via keyboard
- **Nametable mirroring** (horizontal, vertical, single-screen, four-screen)
- **NMI** and **OAM DMA** support
- **PNG screenshot export** in headless mode
- **Pygame UI** for interactive play

## Files

| File | Role |
|------|------|
| `cpu.py` | MOS 6502 CPU core (~750 lines) |
| `ppu.py` | Picture Processing Unit |
| `cartridge.py` | iNES ROM loader + mapper logic |
| `bus.py` | Ties CPU ↔ PPU ↔ RAM ↔ cart ↔ controllers |
| `controller.py` | Standard NES joypad |
| `main.py` | Entry point (pygame + headless modes) |

## Usage

### Play a game (interactive, needs pygame)

```bash
pip install pygame Pillow
python main.py path/to/game.nes
```

Controls:

| NES Button | Keyboard |
|------------|----------|
| A          | X        |
| B          | Z        |
| Select     | Right Shift |
| Start      | Enter |
| D-Pad      | Arrow keys |
| Quit       | Esc |

### Headless mode (save screenshot after N frames)

```bash
python main.py game.nes --headless 60 screenshot.png
```

## Validation

Tested against industry-standard test ROMs:

- ✅ **nestest.nes** — all 8,991 instructions pass, error codes `$02=00 $03=00`
- ✅ **full_palette.nes** — renders colored bands
- ✅ **palette_ram.nes / vbl_clear_time.nes** — text output rendered correctly

## Limitations

- No APU (audio) — games run silent
- Only mappers 0, 2, 3 supported (MMC1, MMC3, etc. not implemented)
- Scanline-accurate, not pixel-cycle-accurate (some split-screen effects may be off)
- Pure Python, but with several hot-path optimisations (see **Performance** below).
  ~25-35 fps on CPython for SMB; use PyPy for 60 fps, or port the hot paths to C.

## Performance

This build contains a number of hot-path rewrites over the naïve reference
implementation. Behaviour is **bit-identical** (framebuffer + CPU cycle counts
verified) — only the execution time changes.

| Test                                | Reference | Optimised | Speed-up |
|-------------------------------------|-----------|-----------|----------|
| SMB headless, 60 frames             | 5.64 s    | 1.73 s    | 3.3×     |
| SMB headless, 200 frames (gameplay) | 27.0 s    | 7.8 s     | 3.5×     |

Key changes:

1. **PPU scheduler** — `ppu.step()` was called 3× per CPU cycle (~1.8 M
   function calls/sec). Replaced with `ppu.advance(n)` that jumps directly to
   the next event boundary (scanline-256 render, sl-241 VBlank, sl-261 clear).
2. **Tile-batched background renderer** — the inner pixel loop now iterates
   over 33 tiles × 8 pixels instead of 256 pixels with per-pixel shifts.
   A 64 K-entry `_TILE_ROW[(hi<<8)|lo]` lookup decodes an entire 8-pixel
   tile row in one table hit. CHR fetches go directly to the cartridge
   bytearray, skipping two layers of indirection.
3. **Bulk framebuffer writes** — the composite loop builds a 256-byte color
   row, then expands it to 768 RGB bytes via one `b''.join(...)` + slice
   copy, replacing 256 three-byte slice writes.
4. **Pre-computed Z/N flag table** — the `_ZN[256]` lookup replaces the
   `set_flag(Z, …); set_flag(N, …)` pair that every arithmetic/load op used
   to call.
5. **Inlined CPU fast paths** — `cpu.read()` short-circuits RAM (< $2000) and
   PRG-ROM (≥ $8000) without going through the bus, and `bus.cpu_read()`
   checks the hottest regions first.
6. **`__slots__`** on `CPU`, `PPU`, `Bus` — faster attribute dispatch.
7. **Kept API compatible** — `bus.step()`, `ppu.step()`, `bus.cpu`, `bus.ram`
   all still work, so `main.py` and `test_nestest.py` are unchanged.

## Architecture Overview

```
         ┌──────────┐
         │   CPU    │  MOS 6502 @ 1.79 MHz
         └────┬─────┘
              │
         ┌────▼─────┐
         │   Bus    │
         └┬────┬───┬┘
          │    │   │
       ┌──▼─┐ ┌▼─┐ ┌▼────────────┐
       │RAM │ │PPU│ │Cartridge (Mappers 0/2/3)│
       └────┘ └───┘ └─────────────┘
                │
                └─► Framebuffer (256×240 RGB)
```

Each CPU cycle triggers 3 PPU dots (NTSC ratio). The PPU renders each
scanline at its end-of-visible dot for simplicity and sets the VBlank flag
at scanline 241, which drives the NMI that most games use to push their
per-frame update logic.

## Extending

- **Add a mapper**: Edit `cartridge.py` and implement `cpu_read`, `cpu_write`, `ppu_read`, `ppu_write` for that mapper number. MMC1 (mapper 1) and MMC3 (mapper 4) unlock ~90% of the library.
- **Add audio**: Implement an APU in `apu.py` and wire it into the `Bus`. The 2A03 APU has 5 channels (2 pulse, 1 triangle, 1 noise, 1 DMC).
- **Save states**: Pickle `bus.cpu.__dict__`, `bus.ppu.__dict__`, and `bus.ram`.
