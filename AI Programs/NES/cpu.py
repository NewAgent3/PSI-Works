"""
NES CPU - Ricoh 2A03 (based on MOS 6502, without decimal mode)
Implements the full official 6502 instruction set with accurate cycle counts.

Performance-optimized rewrite:
- __slots__ everywhere
- Inline RAM & PRG-ROM fast paths in read/write to avoid 3-level indirection
- Precomputed ZN-flag lookup table replaces per-op set_flag(...) pairs
- Addressing-mode and opcode dispatch table built once; step() hoists locals
- Behavior and cycle counts unchanged (nestest-compatible)
"""

# Status flag bits
FLAG_C = 0x01  # Carry
FLAG_Z = 0x02  # Zero
FLAG_I = 0x04  # Interrupt Disable
FLAG_D = 0x08  # Decimal (unused on NES)
FLAG_B = 0x10  # Break
FLAG_U = 0x20  # Unused (always 1)
FLAG_V = 0x40  # Overflow
FLAG_N = 0x80  # Negative

# Precomputed Z/N flag bits for every possible byte value.
# Replaces the per-instruction "set Z, set N" logic with one table lookup.
_ZN = [0] * 256
for _v in range(256):
    f = 0
    if _v == 0:
        f |= FLAG_Z
    if _v & 0x80:
        f |= FLAG_N
    _ZN[_v] = f


class CPU:
    __slots__ = (
        'bus', 'ram', 'cart',
        'a', 'x', 'y', 'sp', 'pc', 'status',
        'cycles', 'total_cycles', 'stall',
        'opcode_table',
    )

    def __init__(self, bus):
        self.bus = bus
        # Cache hot references so read/write can take fast paths without going
        # through self.bus. Set in __init__ since bus/cart/ram exist by now.
        self.ram = bus.ram
        self.cart = bus.cart
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFD
        self.pc = 0
        self.status = 0x24
        self.cycles = 0
        self.total_cycles = 7
        self.stall = 0
        self._build_opcode_table()

    # ---------------- Memory helpers ----------------
    def read(self, addr):
        # Fast paths inline the two hottest memory regions (RAM and PRG-ROM).
        addr &= 0xFFFF
        if addr < 0x2000:
            return self.ram[addr & 0x07FF]
        if addr >= 0x8000:
            return self.cart.cpu_read(addr)
        return self.bus.cpu_read(addr)

    def write(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        if addr < 0x2000:
            self.ram[addr & 0x07FF] = value
        else:
            self.bus.cpu_write(addr, value)

    def read16(self, addr):
        lo = self.read(addr)
        hi = self.read((addr + 1) & 0xFFFF)
        return (hi << 8) | lo

    def read16_bug(self, addr):
        """6502 page-boundary bug on indirect jumps."""
        lo = self.read(addr)
        hi_addr = (addr & 0xFF00) | ((addr + 1) & 0x00FF)
        hi = self.read(hi_addr)
        return (hi << 8) | lo

    # ---------------- Flag helpers ----------------
    def set_flag(self, flag, cond):
        if cond:
            self.status |= flag
        else:
            self.status &= ~flag

    def get_flag(self, flag):
        return 1 if (self.status & flag) else 0

    def set_zn(self, value):
        # Clear Z/N and OR in the precomputed bits for this byte
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[value & 0xFF]

    # ---------------- Stack ----------------
    def push(self, value):
        self.ram[0x100 + self.sp] = value & 0xFF  # stack lives in RAM
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.ram[0x100 + self.sp]

    def push16(self, value):
        self.push((value >> 8) & 0xFF)
        self.push(value & 0xFF)

    def pop16(self):
        lo = self.pop()
        hi = self.pop()
        return (hi << 8) | lo

    # ---------------- Reset / IRQ / NMI ----------------
    def reset(self):
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFD
        self.status = 0x24
        self.pc = self.read16(0xFFFC)
        self.cycles = 7
        self.total_cycles = 7
        self.stall = 0

    def nmi(self):
        self.push16(self.pc)
        self.push((self.status | FLAG_U) & ~FLAG_B)
        self.status |= FLAG_I
        self.pc = self.read16(0xFFFA)
        self.cycles += 7

    def irq(self):
        if self.status & FLAG_I:
            return
        self.push16(self.pc)
        self.push((self.status | FLAG_U) & ~FLAG_B)
        self.status |= FLAG_I
        self.pc = self.read16(0xFFFE)
        self.cycles += 7

    # ---------------- Addressing modes ----------------
    # Each returns (address, page_crossed)
    def am_imp(self):
        return (0, False)

    def am_acc(self):
        return (0, False)

    def am_imm(self):
        addr = self.pc
        self.pc = (self.pc + 1) & 0xFFFF
        return (addr, False)

    def am_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return (addr, False)

    def am_zpx(self):
        addr = (self.read(self.pc) + self.x) & 0xFF
        self.pc = (self.pc + 1) & 0xFFFF
        return (addr, False)

    def am_zpy(self):
        addr = (self.read(self.pc) + self.y) & 0xFF
        self.pc = (self.pc + 1) & 0xFFFF
        return (addr, False)

    def am_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        return (addr, False)

    def am_abx(self):
        base = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        addr = (base + self.x) & 0xFFFF
        crossed = (base & 0xFF00) != (addr & 0xFF00)
        return (addr, crossed)

    def am_aby(self):
        base = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        addr = (base + self.y) & 0xFFFF
        crossed = (base & 0xFF00) != (addr & 0xFF00)
        return (addr, crossed)

    def am_ind(self):
        ptr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        addr = self.read16_bug(ptr)
        return (addr, False)

    def am_izx(self):
        t = (self.read(self.pc) + self.x) & 0xFF
        self.pc = (self.pc + 1) & 0xFFFF
        lo = self.read(t)
        hi = self.read((t + 1) & 0xFF)
        addr = (hi << 8) | lo
        return (addr, False)

    def am_izy(self):
        t = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        lo = self.read(t)
        hi = self.read((t + 1) & 0xFF)
        base = (hi << 8) | lo
        addr = (base + self.y) & 0xFFFF
        crossed = (base & 0xFF00) != (addr & 0xFF00)
        return (addr, crossed)

    def am_rel(self):
        offset = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        if offset & 0x80:
            offset -= 0x100
        addr = (self.pc + offset) & 0xFFFF
        return (addr, False)

    # ---------------- Instructions ----------------
    def op_adc(self, addr, mode):
        m = self.read(addr)
        c = self.status & FLAG_C
        a = self.a
        r = a + m + c
        st = self.status & ~(FLAG_C | FLAG_V | FLAG_Z | FLAG_N)
        if r > 0xFF:
            st |= FLAG_C
        if (~(a ^ m) & (a ^ r)) & 0x80:
            st |= FLAG_V
        self.a = r & 0xFF
        self.status = st | _ZN[self.a]

    def op_sbc(self, addr, mode):
        m = self.read(addr) ^ 0xFF
        c = self.status & FLAG_C
        a = self.a
        r = a + m + c
        st = self.status & ~(FLAG_C | FLAG_V | FLAG_Z | FLAG_N)
        if r > 0xFF:
            st |= FLAG_C
        if (~(a ^ m) & (a ^ r)) & 0x80:
            st |= FLAG_V
        self.a = r & 0xFF
        self.status = st | _ZN[self.a]

    def op_and(self, addr, mode):
        self.a = (self.a & self.read(addr)) & 0xFF
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.a]

    def op_ora(self, addr, mode):
        self.a = (self.a | self.read(addr)) & 0xFF
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.a]

    def op_eor(self, addr, mode):
        self.a = (self.a ^ self.read(addr)) & 0xFF
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.a]

    def op_asl(self, addr, mode):
        if mode == 'acc':
            a = self.a
            self.a = (a << 1) & 0xFF
            self.status = ((self.status & ~(FLAG_C | FLAG_Z | FLAG_N))
                           | (FLAG_C if a & 0x80 else 0)
                           | _ZN[self.a])
        else:
            m = self.read(addr)
            c = FLAG_C if m & 0x80 else 0
            m = (m << 1) & 0xFF
            self.write(addr, m)
            self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c | _ZN[m]

    def op_lsr(self, addr, mode):
        if mode == 'acc':
            a = self.a
            self.a = (a >> 1) & 0xFF
            self.status = ((self.status & ~(FLAG_C | FLAG_Z | FLAG_N))
                           | (FLAG_C if a & 0x01 else 0)
                           | _ZN[self.a])
        else:
            m = self.read(addr)
            c = FLAG_C if m & 0x01 else 0
            m = (m >> 1) & 0xFF
            self.write(addr, m)
            self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c | _ZN[m]

    def op_rol(self, addr, mode):
        c_in = self.status & FLAG_C
        if mode == 'acc':
            a = self.a
            self.a = ((a << 1) | c_in) & 0xFF
            self.status = ((self.status & ~(FLAG_C | FLAG_Z | FLAG_N))
                           | (FLAG_C if a & 0x80 else 0)
                           | _ZN[self.a])
        else:
            m = self.read(addr)
            c_out = FLAG_C if m & 0x80 else 0
            m = ((m << 1) | c_in) & 0xFF
            self.write(addr, m)
            self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c_out | _ZN[m]

    def op_ror(self, addr, mode):
        c_in = (self.status & FLAG_C) << 7
        if mode == 'acc':
            a = self.a
            self.a = ((a >> 1) | c_in) & 0xFF
            self.status = ((self.status & ~(FLAG_C | FLAG_Z | FLAG_N))
                           | (FLAG_C if a & 0x01 else 0)
                           | _ZN[self.a])
        else:
            m = self.read(addr)
            c_out = FLAG_C if m & 0x01 else 0
            m = ((m >> 1) | c_in) & 0xFF
            self.write(addr, m)
            self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c_out | _ZN[m]

    def op_bit(self, addr, mode):
        m = self.read(addr)
        st = self.status & ~(FLAG_Z | FLAG_N | FLAG_V)
        if (self.a & m) == 0:
            st |= FLAG_Z
        if m & 0x80:
            st |= FLAG_N
        if m & 0x40:
            st |= FLAG_V
        self.status = st

    def op_cmp(self, addr, mode):
        m = self.read(addr)
        r = (self.a - m) & 0xFF
        st = self.status & ~(FLAG_C | FLAG_Z | FLAG_N)
        if self.a >= m:
            st |= FLAG_C
        self.status = st | _ZN[r]

    def op_cpx(self, addr, mode):
        m = self.read(addr)
        r = (self.x - m) & 0xFF
        st = self.status & ~(FLAG_C | FLAG_Z | FLAG_N)
        if self.x >= m:
            st |= FLAG_C
        self.status = st | _ZN[r]

    def op_cpy(self, addr, mode):
        m = self.read(addr)
        r = (self.y - m) & 0xFF
        st = self.status & ~(FLAG_C | FLAG_Z | FLAG_N)
        if self.y >= m:
            st |= FLAG_C
        self.status = st | _ZN[r]

    def op_inc(self, addr, mode):
        m = (self.read(addr) + 1) & 0xFF
        self.write(addr, m)
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[m]

    def op_dec(self, addr, mode):
        m = (self.read(addr) - 1) & 0xFF
        self.write(addr, m)
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[m]

    def op_inx(self, addr, mode):
        self.x = (self.x + 1) & 0xFF
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.x]

    def op_iny(self, addr, mode):
        self.y = (self.y + 1) & 0xFF
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.y]

    def op_dex(self, addr, mode):
        self.x = (self.x - 1) & 0xFF
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.x]

    def op_dey(self, addr, mode):
        self.y = (self.y - 1) & 0xFF
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.y]

    def op_lda(self, addr, mode):
        self.a = self.read(addr)
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.a]

    def op_ldx(self, addr, mode):
        self.x = self.read(addr)
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.x]

    def op_ldy(self, addr, mode):
        self.y = self.read(addr)
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.y]

    def op_sta(self, addr, mode):
        self.write(addr, self.a)

    def op_stx(self, addr, mode):
        self.write(addr, self.x)

    def op_sty(self, addr, mode):
        self.write(addr, self.y)

    def op_tax(self, addr, mode):
        self.x = self.a
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.x]

    def op_tay(self, addr, mode):
        self.y = self.a
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.y]

    def op_txa(self, addr, mode):
        self.a = self.x
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.a]

    def op_tya(self, addr, mode):
        self.a = self.y
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.a]

    def op_tsx(self, addr, mode):
        self.x = self.sp
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.x]

    def op_txs(self, addr, mode):
        self.sp = self.x

    def op_pha(self, addr, mode):
        self.push(self.a)

    def op_php(self, addr, mode):
        self.push(self.status | FLAG_B | FLAG_U)

    def op_pla(self, addr, mode):
        self.a = self.pop()
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[self.a]

    def op_plp(self, addr, mode):
        self.status = (self.pop() & ~FLAG_B) | FLAG_U

    def op_jmp(self, addr, mode):
        self.pc = addr

    def op_jsr(self, addr, mode):
        self.push16((self.pc - 1) & 0xFFFF)
        self.pc = addr

    def op_rts(self, addr, mode):
        self.pc = (self.pop16() + 1) & 0xFFFF

    def op_rti(self, addr, mode):
        self.status = (self.pop() & ~FLAG_B) | FLAG_U
        self.pc = self.pop16()

    def op_brk(self, addr, mode):
        self.pc = (self.pc + 1) & 0xFFFF
        self.push16(self.pc)
        self.push(self.status | FLAG_B | FLAG_U)
        self.status |= FLAG_I
        self.pc = self.read16(0xFFFE)

    def op_clc(self, addr, mode): self.status &= ~FLAG_C
    def op_sec(self, addr, mode): self.status |= FLAG_C
    def op_cli(self, addr, mode): self.status &= ~FLAG_I
    def op_sei(self, addr, mode): self.status |= FLAG_I
    def op_clv(self, addr, mode): self.status &= ~FLAG_V
    def op_cld(self, addr, mode): self.status &= ~FLAG_D
    def op_sed(self, addr, mode): self.status |= FLAG_D
    def op_nop(self, addr, mode): pass

    # Branch instructions
    def _branch(self, addr, cond):
        if cond:
            self.cycles += 1
            if (self.pc & 0xFF00) != (addr & 0xFF00):
                self.cycles += 1
            self.pc = addr

    def op_bcc(self, addr, mode): self._branch(addr, not (self.status & FLAG_C))
    def op_bcs(self, addr, mode): self._branch(addr, self.status & FLAG_C)
    def op_beq(self, addr, mode): self._branch(addr, self.status & FLAG_Z)
    def op_bne(self, addr, mode): self._branch(addr, not (self.status & FLAG_Z))
    def op_bmi(self, addr, mode): self._branch(addr, self.status & FLAG_N)
    def op_bpl(self, addr, mode): self._branch(addr, not (self.status & FLAG_N))
    def op_bvc(self, addr, mode): self._branch(addr, not (self.status & FLAG_V))
    def op_bvs(self, addr, mode): self._branch(addr, self.status & FLAG_V)

    # Unofficial / illegal opcodes (common subset)
    def op_lax(self, addr, mode):
        v = self.read(addr)
        self.a = v
        self.x = v
        self.status = (self.status & ~(FLAG_Z | FLAG_N)) | _ZN[v]

    def op_sax(self, addr, mode):
        self.write(addr, self.a & self.x)

    def op_dcp(self, addr, mode):
        m = (self.read(addr) - 1) & 0xFF
        self.write(addr, m)
        r = (self.a - m) & 0xFF
        st = self.status & ~(FLAG_C | FLAG_Z | FLAG_N)
        if self.a >= m:
            st |= FLAG_C
        self.status = st | _ZN[r]

    def op_isb(self, addr, mode):
        m = (self.read(addr) + 1) & 0xFF
        self.write(addr, m)
        m2 = m ^ 0xFF
        c = self.status & FLAG_C
        a = self.a
        r = a + m2 + c
        st = self.status & ~(FLAG_C | FLAG_V | FLAG_Z | FLAG_N)
        if r > 0xFF:
            st |= FLAG_C
        if (~(a ^ m2) & (a ^ r)) & 0x80:
            st |= FLAG_V
        self.a = r & 0xFF
        self.status = st | _ZN[self.a]

    def op_slo(self, addr, mode):
        m = self.read(addr)
        c = FLAG_C if m & 0x80 else 0
        m = (m << 1) & 0xFF
        self.write(addr, m)
        self.a = (self.a | m) & 0xFF
        self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c | _ZN[self.a]

    def op_rla(self, addr, mode):
        c_in = self.status & FLAG_C
        m = self.read(addr)
        c_out = FLAG_C if m & 0x80 else 0
        m = ((m << 1) | c_in) & 0xFF
        self.write(addr, m)
        self.a = (self.a & m) & 0xFF
        self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c_out | _ZN[self.a]

    def op_sre(self, addr, mode):
        m = self.read(addr)
        c = FLAG_C if m & 0x01 else 0
        m = (m >> 1) & 0xFF
        self.write(addr, m)
        self.a = (self.a ^ m) & 0xFF
        self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c | _ZN[self.a]

    def op_rra(self, addr, mode):
        c_in = (self.status & FLAG_C) << 7
        m = self.read(addr)
        c_out = FLAG_C if m & 0x01 else 0
        m = ((m >> 1) | c_in) & 0xFF
        self.write(addr, m)
        # ADC m
        c = c_out  # note: after the shift, carry is ROR-out; that becomes ADC's carry-in
        self.status = (self.status & ~FLAG_C) | c_out
        a = self.a
        r = a + m + (self.status & FLAG_C)
        st = self.status & ~(FLAG_C | FLAG_V | FLAG_Z | FLAG_N)
        if r > 0xFF:
            st |= FLAG_C
        if (~(a ^ m) & (a ^ r)) & 0x80:
            st |= FLAG_V
        self.a = r & 0xFF
        self.status = st | _ZN[self.a]

    def op_anc(self, addr, mode):
        self.a = (self.a & self.read(addr)) & 0xFF
        st = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | _ZN[self.a]
        if self.a & 0x80:
            st |= FLAG_C
        self.status = st

    def op_alr(self, addr, mode):
        self.a = (self.a & self.read(addr)) & 0xFF
        c = FLAG_C if self.a & 0x01 else 0
        self.a = (self.a >> 1) & 0xFF
        self.status = (self.status & ~(FLAG_C | FLAG_Z | FLAG_N)) | c | _ZN[self.a]

    def op_arr(self, addr, mode):
        self.a = (self.a & self.read(addr)) & 0xFF
        c_in = (self.status & FLAG_C) << 7
        self.a = ((self.a >> 1) | c_in) & 0xFF
        st = (self.status & ~(FLAG_C | FLAG_V | FLAG_Z | FLAG_N)) | _ZN[self.a]
        if self.a & 0x40:
            st |= FLAG_C
        if ((self.a >> 6) ^ (self.a >> 5)) & 1:
            st |= FLAG_V
        self.status = st

    def op_axs(self, addr, mode):
        m = self.read(addr)
        t = (self.a & self.x) - m
        st = self.status & ~(FLAG_C | FLAG_Z | FLAG_N)
        if t >= 0:
            st |= FLAG_C
        self.x = t & 0xFF
        self.status = st | _ZN[self.x]

    def op_kil(self, addr, mode):
        # Halt the CPU; treat as nop to avoid hanging
        pass

    # ---------------- Opcode table ----------------
    def _build_opcode_table(self):
        am = {
            'imp': self.am_imp, 'acc': self.am_acc, 'imm': self.am_imm,
            'zp': self.am_zp, 'zpx': self.am_zpx, 'zpy': self.am_zpy,
            'abs': self.am_abs, 'abx': self.am_abx, 'aby': self.am_aby,
            'ind': self.am_ind, 'izx': self.am_izx, 'izy': self.am_izy,
            'rel': self.am_rel,
        }
        t = [None] * 256

        def add(op, handler, mode, cycles, pageadd=False):
            t[op] = (handler, am[mode], mode, cycles, pageadd)

        # --- Official opcodes ---
        # ADC
        add(0x69, self.op_adc, 'imm', 2); add(0x65, self.op_adc, 'zp', 3)
        add(0x75, self.op_adc, 'zpx', 4); add(0x6D, self.op_adc, 'abs', 4)
        add(0x7D, self.op_adc, 'abx', 4, True); add(0x79, self.op_adc, 'aby', 4, True)
        add(0x61, self.op_adc, 'izx', 6); add(0x71, self.op_adc, 'izy', 5, True)
        # SBC
        add(0xE9, self.op_sbc, 'imm', 2); add(0xEB, self.op_sbc, 'imm', 2)
        add(0xE5, self.op_sbc, 'zp', 3); add(0xF5, self.op_sbc, 'zpx', 4)
        add(0xED, self.op_sbc, 'abs', 4); add(0xFD, self.op_sbc, 'abx', 4, True)
        add(0xF9, self.op_sbc, 'aby', 4, True); add(0xE1, self.op_sbc, 'izx', 6)
        add(0xF1, self.op_sbc, 'izy', 5, True)
        # AND
        add(0x29, self.op_and, 'imm', 2); add(0x25, self.op_and, 'zp', 3)
        add(0x35, self.op_and, 'zpx', 4); add(0x2D, self.op_and, 'abs', 4)
        add(0x3D, self.op_and, 'abx', 4, True); add(0x39, self.op_and, 'aby', 4, True)
        add(0x21, self.op_and, 'izx', 6); add(0x31, self.op_and, 'izy', 5, True)
        # ORA
        add(0x09, self.op_ora, 'imm', 2); add(0x05, self.op_ora, 'zp', 3)
        add(0x15, self.op_ora, 'zpx', 4); add(0x0D, self.op_ora, 'abs', 4)
        add(0x1D, self.op_ora, 'abx', 4, True); add(0x19, self.op_ora, 'aby', 4, True)
        add(0x01, self.op_ora, 'izx', 6); add(0x11, self.op_ora, 'izy', 5, True)
        # EOR
        add(0x49, self.op_eor, 'imm', 2); add(0x45, self.op_eor, 'zp', 3)
        add(0x55, self.op_eor, 'zpx', 4); add(0x4D, self.op_eor, 'abs', 4)
        add(0x5D, self.op_eor, 'abx', 4, True); add(0x59, self.op_eor, 'aby', 4, True)
        add(0x41, self.op_eor, 'izx', 6); add(0x51, self.op_eor, 'izy', 5, True)
        # ASL / LSR / ROL / ROR
        add(0x0A, self.op_asl, 'acc', 2); add(0x06, self.op_asl, 'zp', 5)
        add(0x16, self.op_asl, 'zpx', 6); add(0x0E, self.op_asl, 'abs', 6)
        add(0x1E, self.op_asl, 'abx', 7)
        add(0x4A, self.op_lsr, 'acc', 2); add(0x46, self.op_lsr, 'zp', 5)
        add(0x56, self.op_lsr, 'zpx', 6); add(0x4E, self.op_lsr, 'abs', 6)
        add(0x5E, self.op_lsr, 'abx', 7)
        add(0x2A, self.op_rol, 'acc', 2); add(0x26, self.op_rol, 'zp', 5)
        add(0x36, self.op_rol, 'zpx', 6); add(0x2E, self.op_rol, 'abs', 6)
        add(0x3E, self.op_rol, 'abx', 7)
        add(0x6A, self.op_ror, 'acc', 2); add(0x66, self.op_ror, 'zp', 5)
        add(0x76, self.op_ror, 'zpx', 6); add(0x6E, self.op_ror, 'abs', 6)
        add(0x7E, self.op_ror, 'abx', 7)
        # BIT
        add(0x24, self.op_bit, 'zp', 3); add(0x2C, self.op_bit, 'abs', 4)
        # CMP / CPX / CPY
        add(0xC9, self.op_cmp, 'imm', 2); add(0xC5, self.op_cmp, 'zp', 3)
        add(0xD5, self.op_cmp, 'zpx', 4); add(0xCD, self.op_cmp, 'abs', 4)
        add(0xDD, self.op_cmp, 'abx', 4, True); add(0xD9, self.op_cmp, 'aby', 4, True)
        add(0xC1, self.op_cmp, 'izx', 6); add(0xD1, self.op_cmp, 'izy', 5, True)
        add(0xE0, self.op_cpx, 'imm', 2); add(0xE4, self.op_cpx, 'zp', 3); add(0xEC, self.op_cpx, 'abs', 4)
        add(0xC0, self.op_cpy, 'imm', 2); add(0xC4, self.op_cpy, 'zp', 3); add(0xCC, self.op_cpy, 'abs', 4)
        # INC / DEC
        add(0xE6, self.op_inc, 'zp', 5); add(0xF6, self.op_inc, 'zpx', 6)
        add(0xEE, self.op_inc, 'abs', 6); add(0xFE, self.op_inc, 'abx', 7)
        add(0xC6, self.op_dec, 'zp', 5); add(0xD6, self.op_dec, 'zpx', 6)
        add(0xCE, self.op_dec, 'abs', 6); add(0xDE, self.op_dec, 'abx', 7)
        # INX/INY/DEX/DEY
        add(0xE8, self.op_inx, 'imp', 2); add(0xC8, self.op_iny, 'imp', 2)
        add(0xCA, self.op_dex, 'imp', 2); add(0x88, self.op_dey, 'imp', 2)
        # LDA / LDX / LDY
        add(0xA9, self.op_lda, 'imm', 2); add(0xA5, self.op_lda, 'zp', 3)
        add(0xB5, self.op_lda, 'zpx', 4); add(0xAD, self.op_lda, 'abs', 4)
        add(0xBD, self.op_lda, 'abx', 4, True); add(0xB9, self.op_lda, 'aby', 4, True)
        add(0xA1, self.op_lda, 'izx', 6); add(0xB1, self.op_lda, 'izy', 5, True)
        add(0xA2, self.op_ldx, 'imm', 2); add(0xA6, self.op_ldx, 'zp', 3)
        add(0xB6, self.op_ldx, 'zpy', 4); add(0xAE, self.op_ldx, 'abs', 4)
        add(0xBE, self.op_ldx, 'aby', 4, True)
        add(0xA0, self.op_ldy, 'imm', 2); add(0xA4, self.op_ldy, 'zp', 3)
        add(0xB4, self.op_ldy, 'zpx', 4); add(0xAC, self.op_ldy, 'abs', 4)
        add(0xBC, self.op_ldy, 'abx', 4, True)
        # STA / STX / STY
        add(0x85, self.op_sta, 'zp', 3); add(0x95, self.op_sta, 'zpx', 4)
        add(0x8D, self.op_sta, 'abs', 4); add(0x9D, self.op_sta, 'abx', 5)
        add(0x99, self.op_sta, 'aby', 5); add(0x81, self.op_sta, 'izx', 6)
        add(0x91, self.op_sta, 'izy', 6)
        add(0x86, self.op_stx, 'zp', 3); add(0x96, self.op_stx, 'zpy', 4); add(0x8E, self.op_stx, 'abs', 4)
        add(0x84, self.op_sty, 'zp', 3); add(0x94, self.op_sty, 'zpx', 4); add(0x8C, self.op_sty, 'abs', 4)
        # Transfers / stack
        add(0xAA, self.op_tax, 'imp', 2); add(0xA8, self.op_tay, 'imp', 2)
        add(0x8A, self.op_txa, 'imp', 2); add(0x98, self.op_tya, 'imp', 2)
        add(0xBA, self.op_tsx, 'imp', 2); add(0x9A, self.op_txs, 'imp', 2)
        add(0x48, self.op_pha, 'imp', 3); add(0x08, self.op_php, 'imp', 3)
        add(0x68, self.op_pla, 'imp', 4); add(0x28, self.op_plp, 'imp', 4)
        # Jumps / returns
        add(0x4C, self.op_jmp, 'abs', 3); add(0x6C, self.op_jmp, 'ind', 5)
        add(0x20, self.op_jsr, 'abs', 6); add(0x60, self.op_rts, 'imp', 6)
        add(0x40, self.op_rti, 'imp', 6); add(0x00, self.op_brk, 'imp', 7)
        # Flags
        add(0x18, self.op_clc, 'imp', 2); add(0x38, self.op_sec, 'imp', 2)
        add(0x58, self.op_cli, 'imp', 2); add(0x78, self.op_sei, 'imp', 2)
        add(0xB8, self.op_clv, 'imp', 2); add(0xD8, self.op_cld, 'imp', 2)
        add(0xF8, self.op_sed, 'imp', 2); add(0xEA, self.op_nop, 'imp', 2)
        # Branches
        add(0x90, self.op_bcc, 'rel', 2); add(0xB0, self.op_bcs, 'rel', 2)
        add(0xF0, self.op_beq, 'rel', 2); add(0xD0, self.op_bne, 'rel', 2)
        add(0x30, self.op_bmi, 'rel', 2); add(0x10, self.op_bpl, 'rel', 2)
        add(0x50, self.op_bvc, 'rel', 2); add(0x70, self.op_bvs, 'rel', 2)

        # --- Unofficial opcodes ---
        for op in (0x1A, 0x3A, 0x5A, 0x7A, 0xDA, 0xFA):
            add(op, self.op_nop, 'imp', 2)
        for op in (0x80, 0x82, 0x89, 0xC2, 0xE2):
            add(op, self.op_nop, 'imm', 2)
        for op in (0x04, 0x44, 0x64):
            add(op, self.op_nop, 'zp', 3)
        for op in (0x14, 0x34, 0x54, 0x74, 0xD4, 0xF4):
            add(op, self.op_nop, 'zpx', 4)
        add(0x0C, self.op_nop, 'abs', 4)
        for op in (0x1C, 0x3C, 0x5C, 0x7C, 0xDC, 0xFC):
            add(op, self.op_nop, 'abx', 4, True)

        # LAX
        add(0xA3, self.op_lax, 'izx', 6); add(0xA7, self.op_lax, 'zp', 3)
        add(0xAF, self.op_lax, 'abs', 4); add(0xB3, self.op_lax, 'izy', 5, True)
        add(0xB7, self.op_lax, 'zpy', 4); add(0xBF, self.op_lax, 'aby', 4, True)
        # SAX
        add(0x83, self.op_sax, 'izx', 6); add(0x87, self.op_sax, 'zp', 3)
        add(0x8F, self.op_sax, 'abs', 4); add(0x97, self.op_sax, 'zpy', 4)
        # DCP
        add(0xC3, self.op_dcp, 'izx', 8); add(0xC7, self.op_dcp, 'zp', 5)
        add(0xCF, self.op_dcp, 'abs', 6); add(0xD3, self.op_dcp, 'izy', 8)
        add(0xD7, self.op_dcp, 'zpx', 6); add(0xDB, self.op_dcp, 'aby', 7)
        add(0xDF, self.op_dcp, 'abx', 7)
        # ISB
        add(0xE3, self.op_isb, 'izx', 8); add(0xE7, self.op_isb, 'zp', 5)
        add(0xEF, self.op_isb, 'abs', 6); add(0xF3, self.op_isb, 'izy', 8)
        add(0xF7, self.op_isb, 'zpx', 6); add(0xFB, self.op_isb, 'aby', 7)
        add(0xFF, self.op_isb, 'abx', 7)
        # SLO
        add(0x03, self.op_slo, 'izx', 8); add(0x07, self.op_slo, 'zp', 5)
        add(0x0F, self.op_slo, 'abs', 6); add(0x13, self.op_slo, 'izy', 8)
        add(0x17, self.op_slo, 'zpx', 6); add(0x1B, self.op_slo, 'aby', 7)
        add(0x1F, self.op_slo, 'abx', 7)
        # RLA
        add(0x23, self.op_rla, 'izx', 8); add(0x27, self.op_rla, 'zp', 5)
        add(0x2F, self.op_rla, 'abs', 6); add(0x33, self.op_rla, 'izy', 8)
        add(0x37, self.op_rla, 'zpx', 6); add(0x3B, self.op_rla, 'aby', 7)
        add(0x3F, self.op_rla, 'abx', 7)
        # SRE
        add(0x43, self.op_sre, 'izx', 8); add(0x47, self.op_sre, 'zp', 5)
        add(0x4F, self.op_sre, 'abs', 6); add(0x53, self.op_sre, 'izy', 8)
        add(0x57, self.op_sre, 'zpx', 6); add(0x5B, self.op_sre, 'aby', 7)
        add(0x5F, self.op_sre, 'abx', 7)
        # RRA
        add(0x63, self.op_rra, 'izx', 8); add(0x67, self.op_rra, 'zp', 5)
        add(0x6F, self.op_rra, 'abs', 6); add(0x73, self.op_rra, 'izy', 8)
        add(0x77, self.op_rra, 'zpx', 6); add(0x7B, self.op_rra, 'aby', 7)
        add(0x7F, self.op_rra, 'abx', 7)
        # ANC / ALR / ARR / AXS
        add(0x0B, self.op_anc, 'imm', 2); add(0x2B, self.op_anc, 'imm', 2)
        add(0x4B, self.op_alr, 'imm', 2); add(0x6B, self.op_arr, 'imm', 2)
        add(0xCB, self.op_axs, 'imm', 2)
        # KIL (halt)
        for op in (0x02, 0x12, 0x22, 0x32, 0x42, 0x52, 0x62, 0x72, 0x92, 0xB2, 0xD2, 0xF2):
            add(op, self.op_kil, 'imp', 2)

        # Fill any remaining slots with NOP (safety net)
        for i in range(256):
            if t[i] is None:
                t[i] = (self.op_nop, am['imp'], 'imp', 2, False)

        self.opcode_table = t

    # ---------------- Step ----------------
    def step(self):
        if self.stall > 0:
            self.stall -= 1
            self.total_cycles += 1
            return 1

        # Hoist hot fields into locals for the entire instruction
        pc = self.pc
        # Inline the opcode fetch (always falls in RAM or PRG-ROM)
        if pc < 0x2000:
            opcode = self.ram[pc & 0x07FF]
        elif pc >= 0x8000:
            opcode = self.cart.cpu_read(pc)
        else:
            opcode = self.bus.cpu_read(pc)
        self.pc = (pc + 1) & 0xFFFF

        handler, addr_mode_fn, mode_key, base_cycles, pageadd = self.opcode_table[opcode]
        addr, crossed = addr_mode_fn()
        cycles = base_cycles
        if pageadd and crossed:
            cycles += 1
        self.cycles = cycles
        handler(addr, mode_key)
        self.total_cycles += self.cycles
        return self.cycles
