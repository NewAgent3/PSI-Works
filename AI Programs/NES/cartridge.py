"""
NES Cartridge / iNES ROM loader with basic mappers (0, 2, 3).
"""

MIRROR_HORIZONTAL = 0
MIRROR_VERTICAL = 1
MIRROR_SINGLE0 = 2
MIRROR_SINGLE1 = 3
MIRROR_FOUR = 4


class Cartridge:
    def __init__(self, path):
        with open(path, 'rb') as f:
            data = f.read()

        if data[0:4] != b'NES\x1a':
            raise ValueError("Not an iNES file")

        prg_banks = data[4]     # 16KB units
        chr_banks = data[5]     # 8KB units
        flags6 = data[6]
        flags7 = data[7]

        self.mapper = (flags7 & 0xF0) | (flags6 >> 4)
        if flags6 & 0x08:
            self.mirroring = MIRROR_FOUR
        else:
            self.mirroring = MIRROR_VERTICAL if (flags6 & 0x01) else MIRROR_HORIZONTAL
        self.has_battery = bool(flags6 & 0x02)
        has_trainer = bool(flags6 & 0x04)

        offset = 16
        if has_trainer:
            offset += 512

        prg_size = prg_banks * 16384
        self.prg = bytearray(data[offset:offset + prg_size])
        offset += prg_size

        if chr_banks == 0:
            # Uses CHR RAM
            self.chr = bytearray(8192)
            self.chr_is_ram = True
        else:
            chr_size = chr_banks * 8192
            self.chr = bytearray(data[offset:offset + chr_size])
            self.chr_is_ram = False

        self.prg_banks = prg_banks
        self.chr_banks = chr_banks

        # Mapper state
        self.prg_bank_select = 0  # Mapper 2
        self.chr_bank_select = 0  # Mapper 3

        if self.mapper not in (0, 2, 3):
            print(f"[WARN] Mapper {self.mapper} not fully supported; trying mapper 0 fallback")

    # ---------------- CPU-side access (0x8000-0xFFFF) ----------------
    def cpu_read(self, addr):
        if self.mapper == 0:
            # NROM: 16KB (mirrored) or 32KB
            if self.prg_banks == 1:
                return self.prg[(addr - 0x8000) & 0x3FFF]
            return self.prg[(addr - 0x8000) & 0x7FFF]
        elif self.mapper == 2:
            # UxROM: $8000-$BFFF switchable, $C000-$FFFF fixed to last bank
            if addr < 0xC000:
                bank = self.prg_bank_select % max(self.prg_banks, 1)
                return self.prg[bank * 0x4000 + (addr - 0x8000)]
            else:
                bank = self.prg_banks - 1
                return self.prg[bank * 0x4000 + (addr - 0xC000)]
        elif self.mapper == 3:
            # CNROM: PRG like NROM, CHR switchable
            if self.prg_banks == 1:
                return self.prg[(addr - 0x8000) & 0x3FFF]
            return self.prg[(addr - 0x8000) & 0x7FFF]
        # Fallback
        return self.prg[(addr - 0x8000) % len(self.prg)]

    def cpu_write(self, addr, value):
        if self.mapper == 2:
            self.prg_bank_select = value & 0x0F
        elif self.mapper == 3:
            self.chr_bank_select = value & 0x03
        # Mapper 0 is read-only

    # ---------------- PPU-side access (0x0000-0x1FFF) ----------------
    def ppu_read(self, addr):
        if self.mapper == 3 and not self.chr_is_ram:
            bank = self.chr_bank_select % max(self.chr_banks, 1)
            return self.chr[bank * 0x2000 + (addr & 0x1FFF)]
        return self.chr[addr & (len(self.chr) - 1)]

    def ppu_write(self, addr, value):
        if self.chr_is_ram:
            self.chr[addr & (len(self.chr) - 1)] = value & 0xFF
