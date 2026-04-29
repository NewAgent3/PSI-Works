"""
NES Bus - connects CPU, PPU, APU (stub), cartridge, controllers, and RAM.

Performance-optimized rewrite:
- PPU ticks are issued via a single advance(n) call instead of a Python loop,
  eliminating millions of function-call frames per second.
- cpu_read fast-path uses tuple dispatch for the most common address ranges.
- __slots__ for faster attribute access.
"""

from cpu import CPU
from ppu import PPU
from controller import Controller


class Bus:
    __slots__ = (
        'cart', 'ram', 'cpu', 'ppu', 'controllers',
        'dma_page', 'dma_addr', 'dma_data',
        'dma_transfer', 'dma_dummy', 'total_cycles',
    )

    def __init__(self, cartridge):
        self.cart = cartridge
        self.ram = bytearray(2048)   # 2KB internal RAM
        self.cpu = CPU(self)
        self.ppu = PPU(self)
        self.controllers = [Controller(), Controller()]
        self.dma_page = 0
        self.dma_addr = 0
        self.dma_data = 0
        self.dma_transfer = False
        self.dma_dummy = True
        self.total_cycles = 0

    # ---------------- CPU <-> memory map ----------------
    def cpu_read(self, addr):
        addr &= 0xFFFF
        # Fast path: RAM is the hottest region
        if addr < 0x2000:
            return self.ram[addr & 0x07FF]
        # Fast path: PRG ROM is the next hottest
        if addr >= 0x8000:
            return self.cart.cpu_read(addr)
        if addr < 0x4000:
            return self.ppu.cpu_read_register(addr & 0x2007)
        if addr == 0x4016:
            return self.controllers[0].read() | 0x40
        if addr == 0x4017:
            return self.controllers[1].read() | 0x40
        # APU / IO / expansion / WRAM stubs
        return 0

    def cpu_write(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        if addr < 0x2000:
            self.ram[addr & 0x07FF] = value
        elif addr >= 0x8000:
            self.cart.cpu_write(addr, value)
        elif addr < 0x4000:
            self.ppu.cpu_write_register(addr & 0x2007, value)
        elif addr == 0x4014:
            # OAM DMA
            self.dma_page = value
            self.dma_addr = 0
            self.dma_transfer = True
        elif addr == 0x4016:
            self.controllers[0].write(value)
            self.controllers[1].write(value)
        # Other regions: APU / IO / expansion / WRAM stubs (ignored)

    def reset(self):
        self.cpu.reset()
        self.ppu.scanline = 0
        self.ppu.dot = 0

    # ---------------- DMA ----------------
    def _do_dma(self):
        """Copy 256 bytes from CPU memory page to OAM. 513/514 cycles."""
        page = self.dma_page << 8
        # For pages inside RAM we can do a straight bulk copy; otherwise fall back
        if page + 256 <= 0x2000:
            base = page & 0x07FF
            data = bytes(self.ram[base:base + 256])
        else:
            read = self.cpu_read
            data = bytes(read(page + i) for i in range(256))
        self.ppu.oam_dma(data)
        self.cpu.stall += 513
        self.dma_transfer = False

    # ---------------- Step ----------------
    def step(self):
        """Run one CPU instruction, then 3× PPU dots per CPU cycle."""
        if self.dma_transfer:
            self._do_dma()

        cycles = self.cpu.step()

        # Single advance call instead of a Python loop of ppu.step() × (cycles * 3)
        self.ppu.advance(cycles * 3)

        if self.ppu.nmi_pending:
            self.ppu.nmi_pending = False
            self.cpu.nmi()

        self.total_cycles += cycles
        return cycles
