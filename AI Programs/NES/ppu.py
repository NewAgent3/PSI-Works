"""
NES PPU (Picture Processing Unit) - Ricoh 2C02
Scanline-accurate rendering suitable for most mapper 0/2/3 games.

Performance-optimized rewrite:
- advance(n) jumps multiple dots at once (avoids 1.78M step() calls/sec)
- Background renderer caches tile/attr fetches per 8-pixel boundary
- Pre-baked 3-byte palette → slice-assign into framebuffer
- __slots__ for faster attribute access
- Hot locals inside inner loops
"""

# NES color palette (RGB)
NES_PALETTE = [
    (84, 84, 84),   (0, 30, 116),   (8, 16, 144),   (48, 0, 136),
    (68, 0, 100),   (92, 0, 48),    (84, 4, 0),     (60, 24, 0),
    (32, 42, 0),    (8, 58, 0),     (0, 64, 0),     (0, 60, 0),
    (0, 50, 60),    (0, 0, 0),      (0, 0, 0),      (0, 0, 0),
    (152, 150, 152),(8, 76, 196),   (48, 50, 236),  (92, 30, 228),
    (136, 20, 176), (160, 20, 100), (152, 34, 32),  (120, 60, 0),
    (84, 90, 0),    (40, 114, 0),   (8, 124, 0),    (0, 118, 40),
    (0, 102, 120),  (0, 0, 0),      (0, 0, 0),      (0, 0, 0),
    (236, 238, 236),(76, 154, 236), (120, 124, 236),(176, 98, 236),
    (228, 84, 236), (236, 88, 180), (236, 106, 100),(212, 136, 32),
    (160, 170, 0),  (116, 196, 0),  (76, 208, 32),  (56, 204, 108),
    (56, 180, 204), (60, 60, 60),   (0, 0, 0),      (0, 0, 0),
    (236, 238, 236),(168, 204, 236),(188, 188, 236),(212, 178, 236),
    (236, 174, 236),(236, 174, 212),(236, 180, 176),(228, 196, 144),
    (204, 210, 120),(180, 222, 120),(168, 226, 144),(152, 226, 180),
    (160, 214, 228),(160, 162, 160),(0, 0, 0),      (0, 0, 0),
]

# Pre-packed 3-byte strings for each of the 64 palette entries
_PALETTE_BYTES = [bytes(c) for c in NES_PALETTE]

# Pre-computed tile row decoder: for each (lo_byte, hi_byte) pair, give an
# 8-byte array where each byte is the 2-bit pixel value (bit0 = lo plane,
# bit1 = hi plane). This lets us decode an entire tile row in one lookup
# instead of 8 bit-shifts per pixel.
_TILE_ROW = [None] * 65536
for _lo in range(256):
    for _hi in range(256):
        _row = bytearray(8)
        for _b in range(8):
            _bit = 7 - _b
            _row[_b] = ((_lo >> _bit) & 1) | (((_hi >> _bit) & 1) << 1)
        _TILE_ROW[(_hi << 8) | _lo] = bytes(_row)


class PPU:
    __slots__ = (
        'bus', 'vram', 'palette', 'oam',
        'ctrl', 'mask', 'status', 'oam_addr',
        'v', 't', 'x', 'w',
        'read_buffer', 'nmi_output', 'nmi_occurred', 'nmi_pending',
        'scanline', 'dot', 'frame', 'odd_frame',
        'framebuffer', 'frame_ready',
    )

    def __init__(self, bus):
        self.bus = bus
        self.vram = bytearray(2048)       # 2KB nametable memory
        self.palette = bytearray(32)      # 32-byte palette RAM
        self.oam = bytearray(256)         # 64 sprites × 4 bytes

        self.ctrl = 0
        self.mask = 0
        self.status = 0
        self.oam_addr = 0

        self.v = 0
        self.t = 0
        self.x = 0
        self.w = 0

        self.read_buffer = 0
        self.nmi_output = False
        self.nmi_occurred = False
        self.nmi_pending = False

        self.scanline = 0
        self.dot = 0
        self.frame = 0
        self.odd_frame = False

        self.framebuffer = bytearray(256 * 240 * 3)
        self.frame_ready = False

    # ---------------- CPU register interface ----------------
    def cpu_read_register(self, addr):
        reg = addr & 0x7
        data = 0
        if reg == 2:  # PPUSTATUS
            data = (self.status & 0xE0) | (self.read_buffer & 0x1F)
            self.status &= ~0x80
            self.w = 0
        elif reg == 4:  # OAMDATA
            data = self.oam[self.oam_addr]
        elif reg == 7:  # PPUDATA
            a = self.v & 0x3FFF
            if a < 0x3F00:
                data = self.read_buffer
                self.read_buffer = self._ppu_read(a)
            else:
                data = self._ppu_read(a)
                self.read_buffer = self._ppu_read(a - 0x1000)
            self.v = (self.v + (32 if (self.ctrl & 0x04) else 1)) & 0x7FFF
        return data

    def cpu_write_register(self, addr, value):
        reg = addr & 0x7
        value &= 0xFF
        if reg == 0:
            self.ctrl = value
            self.nmi_output = bool(value & 0x80)
            self.t = (self.t & 0xF3FF) | ((value & 0x03) << 10)
            if self.nmi_output and (self.status & 0x80):
                self.nmi_pending = True
        elif reg == 1:
            self.mask = value
        elif reg == 3:
            self.oam_addr = value
        elif reg == 4:
            self.oam[self.oam_addr] = value
            self.oam_addr = (self.oam_addr + 1) & 0xFF
        elif reg == 5:
            if self.w == 0:
                self.t = (self.t & 0x7FE0) | (value >> 3)
                self.x = value & 0x07
                self.w = 1
            else:
                self.t = (self.t & 0x0C1F) | ((value & 0x07) << 12) | ((value & 0xF8) << 2)
                self.w = 0
        elif reg == 6:
            if self.w == 0:
                self.t = (self.t & 0x00FF) | ((value & 0x3F) << 8)
                self.w = 1
            else:
                self.t = (self.t & 0x7F00) | value
                self.v = self.t
                self.w = 0
        elif reg == 7:
            self._ppu_write(self.v & 0x3FFF, value)
            self.v = (self.v + (32 if (self.ctrl & 0x04) else 1)) & 0x7FFF

    # ---------------- PPU memory map ----------------
    def _mirror_nametable(self, addr):
        addr &= 0x0FFF
        mirror = self.bus.cart.mirroring
        table = addr >> 10          # addr // 0x400
        offset = addr & 0x3FF       # addr % 0x400
        if mirror == 0:     # horizontal
            return (table >> 1) * 0x400 + offset
        elif mirror == 1:   # vertical
            return (table & 1) * 0x400 + offset
        elif mirror == 2:
            return offset
        elif mirror == 3:
            return 0x400 + offset
        else:                       # four-screen
            mapped = table * 0x400 + offset
            return mapped & 0x7FF

    def _ppu_read(self, addr):
        addr &= 0x3FFF
        if addr < 0x2000:
            return self.bus.cart.ppu_read(addr)
        elif addr < 0x3F00:
            return self.vram[self._mirror_nametable(addr)]
        else:
            a = addr & 0x1F
            if a in (0x10, 0x14, 0x18, 0x1C):
                a -= 0x10
            return self.palette[a] & (0x30 if (self.mask & 0x01) else 0x3F)

    def _ppu_write(self, addr, value):
        addr &= 0x3FFF
        value &= 0xFF
        if addr < 0x2000:
            self.bus.cart.ppu_write(addr, value)
        elif addr < 0x3F00:
            self.vram[self._mirror_nametable(addr)] = value
        else:
            a = addr & 0x1F
            if a in (0x10, 0x14, 0x18, 0x1C):
                a -= 0x10
            self.palette[a] = value

    # ---------------- OAM DMA ----------------
    def oam_dma(self, data):
        oa = self.oam_addr
        oam = self.oam
        if oa == 0:
            oam[:] = data
        else:
            for i in range(256):
                oam[(oa + i) & 0xFF] = data[i]

    # ---------------- Rendering ----------------
    def _rendering(self):
        return (self.mask & 0x18) != 0

    def _render_scanline(self, sl):
        """Render one complete scanline into the framebuffer (256 pixels).

        Strategy: decide the final NES color index (0-63) for every pixel into
        a 256-byte row buffer, then build all 768 RGB bytes in one pass via
        ``b''.join()`` over precomputed 3-byte palette entries. That gives us
        a single slice assignment into the framebuffer instead of 256 three-
        byte slice writes.
        """
        if sl < 0 or sl >= 240:
            return

        palette = self.palette
        fb = self.framebuffer
        row_off = sl * 768  # 256 * 3
        universal = palette[0] & 0x3F
        pbytes = _PALETTE_BYTES

        if not self._rendering():
            fb[row_off:row_off + 768] = pbytes[universal] * 256
            return

        # ---- Background pixels (0-15 palette index, opaque flag) ----
        bg_pixels = bytearray(256)
        bg_opaque = bytearray(256)
        if self.mask & 0x08:
            self._render_bg_scanline(sl, bg_pixels, bg_opaque)

        # ---- Sprite pixels ----
        sp_pixels = bytearray(256)
        sp_opaque = bytearray(256)
        sp_priority = bytearray(256)
        sp_is_zero = bytearray(256)
        if self.mask & 0x10:
            self._render_sprites_scanline(sl, sp_pixels, sp_opaque, sp_priority, sp_is_zero)

        mask = self.mask
        show_bg_left = mask & 0x02
        show_sp_left = mask & 0x04
        status = self.status
        sprite_zero_already = status & 0x40

        # Build the 256-entry color-index row in one pass
        color_row = bytearray(256)
        for x in range(256):
            bo = bg_opaque[x]
            so = sp_opaque[x]
            if x < 8:
                if not show_bg_left:
                    bo = 0
                if not show_sp_left:
                    so = 0

            if not bo and not so:
                color_row[x] = universal
            elif not bo and so:
                color_row[x] = palette[0x10 + sp_pixels[x]] & 0x3F
            elif bo and not so:
                color_row[x] = palette[bg_pixels[x]] & 0x3F
            else:
                if sp_is_zero[x] and x != 255 and not sprite_zero_already:
                    status |= 0x40
                    sprite_zero_already = 1
                if sp_priority[x]:
                    color_row[x] = palette[bg_pixels[x]] & 0x3F
                else:
                    color_row[x] = palette[0x10 + sp_pixels[x]] & 0x3F

        # Bulk-expand 256 color indices -> 768 RGB bytes via a single join + slice copy
        fb[row_off:row_off + 768] = b''.join(pbytes[c] for c in color_row)
        self.status = status

    def _render_bg_scanline(self, sl, bg_pixels, bg_opaque):
        """Render background for one scanline, working one full 8-pixel tile at a time.

        Hot-path optimisations:
          * `_TILE_ROW` lookup decodes an entire 8-pixel tile row in one shot.
          * Pattern fetches go straight to the cartridge's CHR bytearray,
            saving a function-call hop on the hottest code path.
        """
        pattern_table = 0x1000 if (self.ctrl & 0x10) else 0x0000
        scroll_x = ((self.t & 0x1F) << 3) | self.x
        scroll_y_fine = (self.t >> 12) & 0x07
        scroll_y_coarse = (self.t >> 5) & 0x1F
        base_nt = (self.t >> 10) & 0x03

        y = sl + scroll_y_coarse * 8 + scroll_y_fine
        nt_v = (base_nt >> 1) & 1
        if y >= 240:
            y -= 240
            nt_v ^= 1
        tile_row = (y >> 3) & 0x1F
        fine_y = y & 7

        ppu_read = self._ppu_read
        cart = self.bus.cart
        mapper = cart.mapper
        if mapper == 3 and not cart.chr_is_ram:
            chr_bank_base = (cart.chr_bank_select % max(cart.chr_banks, 1)) * 0x2000
            chr_bank_mode = True
        else:
            chr_bank_base = 0
            chr_bank_mode = False
        chr_mem = cart.chr
        chr_mask = len(chr_mem) - 1

        tile_row_tbl = _TILE_ROW
        nt_h_base = base_nt & 1

        start_fine = scroll_x & 7
        first_tile_col = (scroll_x >> 3) & 0x1F
        first_nt_h_flip = (scroll_x >> 8) & 1

        px = 0
        for t_idx in range(33):
            global_col = first_tile_col + t_idx
            nt_h = nt_h_base ^ first_nt_h_flip
            if global_col >= 32:
                global_col -= 32
                nt_h ^= 1
            tile_col = global_col

            nt_select = (nt_v << 1) | nt_h
            nt_base = 0x2000 + nt_select * 0x400
            tile_id = ppu_read(nt_base + tile_row * 32 + tile_col)
            attr = ppu_read(nt_base + 0x3C0 + (tile_row >> 2) * 8 + (tile_col >> 2))
            shift = ((tile_row & 0x02) << 1) | (tile_col & 0x02)
            palette_hi_shifted = ((attr >> shift) & 0x03) << 2

            # Pattern fetch: skip the _ppu_read + cart.ppu_read hops
            tile_addr = pattern_table + tile_id * 16 + fine_y
            if chr_bank_mode:
                lo = chr_mem[chr_bank_base + (tile_addr & 0x1FFF)]
                hi = chr_mem[chr_bank_base + ((tile_addr + 8) & 0x1FFF)]
            else:
                lo = chr_mem[tile_addr & chr_mask]
                hi = chr_mem[(tile_addr + 8) & chr_mask]
            row_bytes = tile_row_tbl[(hi << 8) | lo]

            start_b = start_fine if t_idx == 0 else 0
            end_b = 8
            remaining = 256 - px
            if (end_b - start_b) > remaining:
                end_b = start_b + remaining

            for b in range(start_b, end_b):
                p = row_bytes[b]
                if p:
                    bg_pixels[px] = palette_hi_shifted | p
                    bg_opaque[px] = 1
                px += 1

            if px >= 256:
                break

    def _render_sprites_scanline(self, sl, sp_pixels, sp_opaque, sp_priority, sp_is_zero):
        sprite_height = 16 if (self.ctrl & 0x20) else 8
        sprite_pattern = 0x1000 if (self.ctrl & 0x08) else 0x0000

        oam = self.oam
        count = 0
        candidates = []
        for i in range(64):
            y = oam[i * 4]
            if y >= 0xEF:
                continue
            row = sl - y
            if 0 <= row < sprite_height:
                candidates.append(i)
                count += 1
                if count > 8:
                    self.status |= 0x20
                    break

        if not candidates:
            return

        ppu_read = self._ppu_read
        # Render reverse for correct priority (lower sprite index = higher priority)
        for i in reversed(candidates):
            base = i * 4
            y = oam[base]
            tile = oam[base + 1]
            attr = oam[base + 2]
            x_pos = oam[base + 3]
            flip_h = attr & 0x40
            flip_v = attr & 0x80
            behind = attr & 0x20
            pal_hi = (attr & 0x03) << 2

            row = sl - y
            if flip_v:
                row = sprite_height - 1 - row

            if sprite_height == 16:
                pt = (tile & 1) * 0x1000
                tile_idx = tile & 0xFE
                if row >= 8:
                    tile_idx += 1
                    row -= 8
                tile_addr = pt + tile_idx * 16 + row
            else:
                tile_addr = sprite_pattern + tile * 16 + row

            lo = ppu_read(tile_addr)
            hi = ppu_read(tile_addr + 8)

            is_zero = 1 if i == 0 else 0
            priority_flag = 1 if behind else 0

            for xi in range(8):
                sx = x_pos + xi
                if sx >= 256:
                    break
                bit = xi if flip_h else (7 - xi)
                p = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1)
                if p == 0:
                    continue
                sp_pixels[sx] = pal_hi | p
                sp_opaque[sx] = 1
                sp_priority[sx] = priority_flag
                sp_is_zero[sx] = is_zero

    # ---------------- Stepping ----------------
    def step(self):
        """Advance the PPU by one dot. Kept for API compatibility; advance(n) is preferred."""
        self.advance(1)

    def advance(self, n):
        """Advance the PPU by n dots, jumping directly to the next event boundary.

        This replaces the per-dot Python loop with a math-based scheduler, which is
        the single biggest perf win because most dots have no side effects.
        """
        scanline = self.scanline
        dot = self.dot

        while n > 0:
            # Distance to next event (or end of scanline)
            # Events per scanline:
            #   dot 1  on sl=261 -> clear VBlank/sprite-0/overflow
            #   dot 1  on sl=241 -> set VBlank, frame_ready, maybe NMI
            #   dot 256 on sl=0..239 -> render scanline
            # Beyond 340 -> wrap scanline

            # Find next dot-of-interest on this scanline
            next_dot = 341  # end-of-scanline boundary
            if dot < 1:
                # dot 0 -> possibly dot 1 event on sl 241 or 261
                if scanline == 261 or scanline == 241:
                    next_dot = 1
                elif scanline < 240:
                    next_dot = 256
            elif dot < 256 and scanline < 240:
                next_dot = 256
            # Otherwise we skip to 341 (end of scanline)

            step_count = next_dot - dot
            if step_count > n:
                step_count = n
            dot += step_count
            n -= step_count

            # Fire events when we land exactly on them
            if dot == 1:
                if scanline == 261:
                    self.status &= ~0xE0  # clear VBlank, sprite-0, overflow
                    self.nmi_occurred = False
                elif scanline == 241:
                    self.status |= 0x80
                    self.frame_ready = True
                    if self.nmi_output:
                        self.nmi_pending = True
                        self.nmi_occurred = True
            elif dot == 256 and scanline < 240:
                # Persist dot/scanline before rendering in case renderer reads them
                self.dot = dot
                self.scanline = scanline
                self._render_scanline(scanline)

            if dot >= 341:
                dot = 0
                scanline += 1
                if scanline > 261:
                    scanline = 0
                    self.frame += 1
                    self.odd_frame = not self.odd_frame

        self.scanline = scanline
        self.dot = dot
