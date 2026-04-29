"""
NES Emulator main entry point.
Usage:
  python main.py <rom.nes>           # play with pygame (keyboard controls)
  python main.py <rom.nes> --headless N  # run N frames headless, save screenshot
"""

import sys
import os
import time
from cartridge import Cartridge
from bus import Bus
from controller import Controller

KEY_MAP = {
    # pygame keys -> controller button index
    'x': Controller.BUTTON_A,
    'z': Controller.BUTTON_B,
    'rshift': Controller.BUTTON_SELECT,
    'return': Controller.BUTTON_START,
    'up': Controller.BUTTON_UP,
    'down': Controller.BUTTON_DOWN,
    'left': Controller.BUTTON_LEFT,
    'right': Controller.BUTTON_RIGHT,
}


def run_frame(bus):
    """Run the bus until the PPU reports a finished frame."""
    bus.ppu.frame_ready = False
    # Safety cap: a frame is ~29,780 CPU cycles
    safety = 0
    while not bus.ppu.frame_ready and safety < 100000:
        bus.step()
        safety += 1


def save_ppm(path, framebuffer, w=256, h=240):
    with open(path, 'wb') as f:
        f.write(f"P6\n{w} {h}\n255\n".encode())
        f.write(bytes(framebuffer))


def save_png(path, framebuffer, w=256, h=240):
    try:
        from PIL import Image
        img = Image.frombytes('RGB', (w, h), bytes(framebuffer))
        img.save(path)
        return True
    except Exception:
        return False


def run_headless(rom_path, frames=60, out='screenshot.png'):
    cart = Cartridge(rom_path)
    bus = Bus(cart)
    bus.reset()
    start = time.time()
    for i in range(frames):
        run_frame(bus)
    elapsed = time.time() - start
    print(f"Ran {frames} frames in {elapsed:.2f}s ({frames/elapsed:.1f} fps)")
    if not save_png(out, bus.ppu.framebuffer):
        # fall back to PPM
        alt = os.path.splitext(out)[0] + '.ppm'
        save_ppm(alt, bus.ppu.framebuffer)
        print(f"Saved screenshot to {alt}")
    else:
        print(f"Saved screenshot to {out}")


def run_pygame(rom_path, scale=3):
    import pygame
    cart = Cartridge(rom_path)
    bus = Bus(cart)
    bus.reset()

    pygame.init()
    screen = pygame.display.set_mode((256 * scale, 240 * scale))
    pygame.display.set_caption(f"NES - {os.path.basename(rom_path)}")
    clock = pygame.time.Clock()

    key_bindings = {
        pygame.K_x: Controller.BUTTON_A,
        pygame.K_z: Controller.BUTTON_B,
        pygame.K_RSHIFT: Controller.BUTTON_SELECT,
        pygame.K_RETURN: Controller.BUTTON_START,
        pygame.K_UP: Controller.BUTTON_UP,
        pygame.K_DOWN: Controller.BUTTON_DOWN,
        pygame.K_LEFT: Controller.BUTTON_LEFT,
        pygame.K_RIGHT: Controller.BUTTON_RIGHT,
    }

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key in key_bindings:
                    bus.controllers[0].set_button(
                        key_bindings[event.key], True)
            elif event.type == pygame.KEYUP:
                if event.key in key_bindings:
                    bus.controllers[0].set_button(
                        key_bindings[event.key], False)

        run_frame(bus)

        surf = pygame.image.frombuffer(
            bytes(bus.ppu.framebuffer), (256, 240), 'RGB')
        surf = pygame.transform.scale(surf, (256 * scale, 240 * scale))
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    rom = sys.argv[1]
    if '--headless' in sys.argv:
        i = sys.argv.index('--headless')
        frames = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 60
        out = sys.argv[i + 2] if i + 2 < len(sys.argv) else 'screenshot.png'
        run_headless(rom, frames, out)
    else:
        run_pygame(rom)


if __name__ == '__main__':
    main()
