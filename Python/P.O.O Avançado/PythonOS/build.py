#!/usr/bin/env python3
"""
Win2K-OS Build System
=====================
Assembles the bootloader and kernel with NASM, stitches them into
a flat floppy/HDD image, and launches it in QEMU.

Usage:
    python build.py           # build + run
    python build.py --build   # build only
    python build.py --run     # run only (image must exist)
    python build.py --clean   # remove build artefacts
"""

import os
import sys
import shutil
import struct
import subprocess
import argparse
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
SRC_DIR = SCRIPT_DIR / "src"
BUILD_DIR = SCRIPT_DIR / "build"

NASM = Path(r"C:\Users\gatin\AppData\Local\bin\NASM\nasm.exe")
QEMU_DIR = Path(r"C:\Program Files\qemu")
QEMU = QEMU_DIR / "qemu-system-i386.exe"

BOOT_ASM = SRC_DIR / "boot.asm"
KERNEL_ASM = SRC_DIR / "kernel.asm"
BOOT_BIN = BUILD_DIR / "boot.bin"
KERNEL_BIN = BUILD_DIR / "kernel.bin"
DISK_IMG = BUILD_DIR / "win2kos.img"

# Disk geometry (1.44 MB floppy)
SECTOR_SIZE = 512
DISK_SECTORS = 2880          # 1.44 MB
KERNEL_START = 1             # sectors offset from start of disk (0-based)


# ── ANSI colours ─────────────────────────────────────────────────────────────
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"


def banner():
    print(f"""
{C.BLUE}{C.BOLD}╔══════════════════════════════════════════════════════╗
║          Win2K-OS  —  Build System  v1.0             ║
║  Bootloader + Kernel  → Flat Disk Image → QEMU       ║
╚══════════════════════════════════════════════════════╝{C.RESET}
""")


def info(msg): print(f"{C.CYAN}  [*]{C.RESET} {msg}")
def ok(msg): print(f"{C.GREEN}  [✓]{C.RESET} {msg}")
def warn(msg): print(f"{C.YELLOW}  [!]{C.RESET} {msg}")
def fail(msg): print(f"{C.RED}  [✗]{C.RESET} {msg}")
def step(msg): print(f"\n{C.BOLD}{C.BLUE}─── {msg}{C.RESET}")


# ── Tool validation ───────────────────────────────────────────────────────────
def check_tools():
    step("Checking tools")
    ok_flag = True

    if NASM.exists():
        ok(f"NASM found: {NASM}")
    else:
        fail(f"NASM not found at {NASM}")
        fail("  Install NASM and update the NASM path in build.py")
        ok_flag = False

    if QEMU.exists():
        ok(f"QEMU found: {QEMU}")
    else:
        fail(f"QEMU not found at {QEMU}")
        fail("  Install QEMU and update the QEMU_DIR path in build.py")
        ok_flag = False

    if not ok_flag:
        sys.exit(1)


# ── Assembly ──────────────────────────────────────────────────────────────────
def assemble(src: Path, out: Path, origin: int):
    """Run NASM on `src` producing a flat binary at `out`."""
    cmd = [
        str(NASM),
        "-f", "bin",
        f"-Dorg_addr={origin:#06x}",
        "-o", str(out),
        str(src),
    ]
    info(f"Assembling {src.name}  →  {out.name}")
    info(f"  cmd: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        fail(f"NASM error (exit {result.returncode}):")
        for line in result.stdout.splitlines():
            print(f"    {C.YELLOW}{line}{C.RESET}")
        for line in result.stderr.splitlines():
            print(f"    {C.RED}{line}{C.RESET}")
        sys.exit(1)

    size = out.stat().st_size
    ok(f"{out.name} assembled  ({size:,} bytes)")
    return size


# ── Disk image construction ────────────────────────────────────────────────────
def build_image():
    step("Building disk image")

    boot_data = BOOT_BIN.read_bytes()
    kernel_data = KERNEL_BIN.read_bytes()

    # Verify bootloader size
    if len(boot_data) != SECTOR_SIZE:
        fail(f"Bootloader is {len(boot_data)} bytes, expected {SECTOR_SIZE}!")
        fail("  Check for 'times 510-($-$$) db 0' + 0xAA55 in boot.asm")
        sys.exit(1)

    # Verify boot signature
    if boot_data[-2:] != b'\x55\xAA':
        fail("Boot signature (0xAA55) missing from bootloader!")
        sys.exit(1)

    ok(f"Bootloader OK  — boot signature: 55 AA ✓")

    # Pad kernel to whole sectors
    kernel_sectors = (len(kernel_data) + SECTOR_SIZE - 1) // SECTOR_SIZE
    kernel_padded = kernel_data.ljust(kernel_sectors * SECTOR_SIZE, b'\x00')
    info(f"Kernel: {len(kernel_data):,} bytes → {kernel_sectors} sector(s)")

    # Create blank 1.44 MB image
    disk = bytearray(DISK_SECTORS * SECTOR_SIZE)

    # Write bootloader at sector 0
    disk[0:SECTOR_SIZE] = boot_data

    # Write kernel at sector 1
    start = KERNEL_START * SECTOR_SIZE
    disk[start:start + len(kernel_padded)] = kernel_padded

    DISK_IMG.write_bytes(disk)
    ok(f"Disk image written: {DISK_IMG.name}  ({len(disk):,} bytes / {len(disk)//1024} KB)")

    # Quick sanity dump of first bytes
    info(f"  Sector 0 tail: {' '.join(f'{b:02X}' for b in disk[506:512])}")


# ── Build ─────────────────────────────────────────────────────────────────────
def build():
    check_tools()

    step("Creating build directory")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    ok(f"Build dir: {BUILD_DIR}")

    step("Assembling sources")
    assemble(BOOT_ASM,   BOOT_BIN,   0x7C00)
    assemble(KERNEL_ASM, KERNEL_BIN, 0x8000)

    build_image()

    print(f"\n{C.GREEN}{C.BOLD}  Build complete! ✓{C.RESET}")


# ── Run ───────────────────────────────────────────────────────────────────────
def run():
    if not DISK_IMG.exists():
        fail(f"Disk image not found: {DISK_IMG}")
        fail("  Run 'python build.py --build' first")
        sys.exit(1)

    step("Launching QEMU")

    # QEMU cannot handle non-ASCII characters in file paths (e.g. 'ç' in
    # 'Avançado').  Work around this by copying the image to a safe temp
    # location that is guaranteed to be pure ASCII.
    import tempfile
    import shutil as _shutil

    tmp_dir = Path(tempfile.gettempdir()) / "win2kos_run"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_img = tmp_dir / "win2kos.img"

    info(f"Copying image to ASCII-safe temp path:")
    info(f"  {tmp_img}")
    _shutil.copy2(DISK_IMG, tmp_img)
    ok("Image copied.")

    cmd = [
        str(QEMU),
        "-drive", f"file={tmp_img},format=raw,if=floppy",
        "-m",     "32",              # 32 MB RAM
        "-name",  "Win2K-OS",
        "-rtc",   "base=localtime",  # sync RTC to host clock
    ]

    info(f"Command:\n    {' '.join(str(x) for x in cmd)}\n")
    info("QEMU window will open. Press ESC inside the OS to shut down.")
    info("Close the QEMU window to exit emulation.")

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        fail(f"Could not launch QEMU from {QEMU}")
        sys.exit(1)
    except KeyboardInterrupt:
        warn("Build interrupted.")
    finally:
        # Clean up the temp copy
        try:
            tmp_img.unlink(missing_ok=True)
        except Exception:
            pass


# ── Clean ─────────────────────────────────────────────────────────────────────
def clean():
    step("Cleaning build artefacts")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        ok(f"Removed {BUILD_DIR}")
    else:
        info("Nothing to clean.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    banner()

    parser = argparse.ArgumentParser(
        description="Win2K-OS Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--build",  action="store_true",
                        help="Assemble and link only")
    parser.add_argument("--run",    action="store_true",
                        help="Run existing image in QEMU")
    parser.add_argument("--clean",  action="store_true",
                        help="Remove build directory")
    args = parser.parse_args()

    if args.clean:
        clean()
    elif args.build:
        build()
    elif args.run:
        run()
    else:
        # Default: build then run
        build()
        run()


if __name__ == "__main__":
    main()
