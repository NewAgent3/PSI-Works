#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <SDL2/SDL.h>

/* -------------------------------- Constants ------------------------------- */
#define CYCLES_PER_FRAME 70224    /* 4194304 Hz / 59.73 Hz */
#define SCREEN_W 160
#define SCREEN_H 144

/* Memory map */
#define ROM_BANK0  0x0000
#define ROM_BANK1  0x4000
#define VRAM       0x8000
#define CARTRAM    0xA000
#define WRAM       0xC000
#define ECHO       0xE000
#define OAM        0xFE00
#define UNUSED     0xFEA0
#define IO         0xFF00
#define HRAM       0xFF80
#define IE         0xFFFF

/* I/O registers */
#define P1         0xFF00    /* joypad */
#define DIV        0xFF04    /* divider */
#define TIMA       0xFF05    /* timer counter */
#define TMA        0xFF06    /* timer modulo */
#define TAC        0xFF07    /* timer control */
#define IF         0xFF0F    /* interrupt flag */
#define NR52       0xFF26    /* sound on/off */
#define LCDC       0xFF40    /* LCD control */
#define STAT       0xFF41    /* LCD status */
#define SCY        0xFF42    /* scroll Y */
#define SCX        0xFF43    /* scroll X */
#define LY         0xFF44    /* current scanline */
#define LYC        0xFF45    /* compare scanline */
#define DMA        0xFF46    /* DMA transfer */
#define BGP        0xFF47    /* background palette */
#define OBP0       0xFF48    /* object palette 0 */
#define OBP1       0xFF49    /* object palette 1 */
#define WY         0xFF4A    /* window Y */
#define WX         0xFF4B    /* window X */
#define KEY1       0xFF4D    /* prepare speed switch (CGB) */
#define VBK        0xFF4F    /* VRAM bank (CGB) */
#define HDMA1      0xFF51    /* DMA regs (CGB) */
#define HDMA2      0xFF52
#define HDMA3      0xFF53
#define HDMA4      0xFF54
#define HDMA5      0xFF55
#define RP         0xFF56    /* infrared (CGB) */
#define BCPS       0xFF68    /* background color palette spec (CGB) */
#define BCPD       0xFF69    /* background color palette data (CGB) */
#define OCPS       0xFF6A    /* object color palette spec (CGB) */
#define OCPD       0xFF6B    /* object color palette data (CGB) */
#define SVBK       0xFF70    /* WRAM bank (CGB) */

/* -------------------------------- CPU state ------------------------------- */
typedef struct {
    uint8_t a, f, b, c, d, e, h, l;
    uint16_t pc, sp;
    uint64_t cycles;          /* total cycles executed */
    int ime;                   /* interrupt master enable flag */
    int halt;                  /* is CPU halted? */
} cpu_regs;

cpu_regs cpu;

/* -------------------------------- Memory ---------------------------------- */
uint8_t rom[0x8000];          /* 32 KB ROM (no MBC) */
uint8_t vram[0x2000];         /* 8 KB VRAM */
uint8_t cart_ram[0x2000];     /* 8 KB cartridge RAM */
uint8_t wram[0x2000];         /* 8 KB work RAM */
uint8_t oam[0xA0];            /* 160 bytes OAM */
uint8_t hram[0x7F];           /* 127 bytes HRAM (0xFF80-0xFFFE) */
uint8_t io[0x80];             /* I/O registers (0xFF00-0xFF7F) */
uint8_t interrupt_enable;     /* 0xFFFF */

/* Helper: read byte from memory */
uint8_t mem_read(uint16_t addr) {
    if (addr < 0x8000) return rom[addr];                 /* ROM */
    else if (addr < 0xA000) return vram[addr & 0x1FFF];  /* VRAM */
    else if (addr < 0xC000) return cart_ram[addr & 0x1FFF]; /* Cart RAM */
    else if (addr < 0xE000) return wram[addr & 0x1FFF];  /* Work RAM */
    else if (addr < 0xFE00) return wram[addr & 0x1FFF];  /* Echo RAM (mirror) */
    else if (addr < 0xFEA0) return oam[addr & 0xFF];     /* OAM */
    else if (addr < 0xFF00) return 0;                    /* Unusable */
    else if (addr < 0xFF80) return io[addr & 0x7F];      /* I/O registers */
    else if (addr < 0xFFFF) return hram[addr & 0x7F];    /* HRAM */
    else if (addr == 0xFFFF) return interrupt_enable;    /* IE register */
    return 0;
}

/* Helper: write byte to memory */
void mem_write(uint16_t addr, uint8_t val) {
    if (addr < 0x8000) { /* ROM – ignore writes (some cartridges use it for banking) */ }
    else if (addr < 0xA000) { vram[addr & 0x1FFF] = val; }
    else if (addr < 0xC000) { cart_ram[addr & 0x1FFF] = val; }
    else if (addr < 0xE000) { wram[addr & 0x1FFF] = val; }
    else if (addr < 0xFE00) { wram[addr & 0x1FFF] = val; } /* echo */
    else if (addr < 0xFEA0) { oam[addr & 0xFF] = val; }
    else if (addr < 0xFF00) { /* ignore */ }
    else if (addr < 0xFF80) {
        io[addr & 0x7F] = val;
        /* Special handling for DIV reset */
        if (addr == DIV) io[addr & 0x7F] = 0;
        /* DMA transfer (simplified: copy OAM from ROM/RAM) */
        if (addr == DMA) {
            uint16_t src = val << 8;
            for (int i = 0; i < 0xA0; i++)
                oam[i] = mem_read(src + i);
        }
    }
    else if (addr < 0xFFFF) { hram[addr & 0x7F] = val; }
    else if (addr == 0xFFFF) { interrupt_enable = val; }
}

/* -------------------------------- CPU helpers ----------------------------- */
uint16_t get_af() { return (cpu.a << 8) | cpu.f; }
void set_af(uint16_t val) { cpu.a = val >> 8; cpu.f = val & 0xFF; }
uint16_t get_bc() { return (cpu.b << 8) | cpu.c; }
void set_bc(uint16_t val) { cpu.b = val >> 8; cpu.c = val & 0xFF; }
uint16_t get_de() { return (cpu.d << 8) | cpu.e; }
void set_de(uint16_t val) { cpu.d = val >> 8; cpu.e = val & 0xFF; }
uint16_t get_hl() { return (cpu.h << 8) | cpu.l; }
void set_hl(uint16_t val) { cpu.h = val >> 8; cpu.l = val & 0xFF; }

/* Flag bits */
#define FLAG_Z (1 << 7)
#define FLAG_N (1 << 6)
#define FLAG_H (1 << 5)
#define FLAG_C (1 << 4)

/* -------------------------------- CPU instructions ------------------------ */
static uint8_t opcode;       /* current opcode */
static uint8_t imm8;         /* immediate byte */
static uint16_t imm16;       /* immediate word */

/* Fetch next byte and advance PC */
uint8_t fetch8() {
    return mem_read(cpu.pc++);
}

uint16_t fetch16() {
    uint16_t lo = fetch8();
    uint16_t hi = fetch8();
    return (hi << 8) | lo;
}

/* Execute one instruction, return number of cycles */
int cpu_step() {
    if (cpu.halt) {
        /* Halted: do nothing, but still consume cycles */
        cpu.cycles += 4;
        return 4;
    }

    opcode = fetch8();
    uint16_t tmp16;
    uint8_t tmp8;
    int cycles = 4; /* default (most 8-bit ops) */

    switch (opcode) {
        /* ---------- 8-bit loads ---------- */
        case 0x40: cpu.b = cpu.b; break; /* LD B,B */
        case 0x41: cpu.b = cpu.c; break;
        case 0x42: cpu.b = cpu.d; break;
        case 0x43: cpu.b = cpu.e; break;
        case 0x44: cpu.b = cpu.h; break;
        case 0x45: cpu.b = cpu.l; break;
        case 0x46: cpu.b = mem_read(get_hl()); cycles = 8; break;
        case 0x47: cpu.b = cpu.a; break;
        case 0x48: cpu.c = cpu.b; break;
        case 0x49: cpu.c = cpu.c; break;
        case 0x4A: cpu.c = cpu.d; break;
        case 0x4B: cpu.c = cpu.e; break;
        case 0x4C: cpu.c = cpu.h; break;
        case 0x4D: cpu.c = cpu.l; break;
        case 0x4E: cpu.c = mem_read(get_hl()); cycles = 8; break;
        case 0x4F: cpu.c = cpu.a; break;
        case 0x50: cpu.d = cpu.b; break;
        case 0x51: cpu.d = cpu.c; break;
        case 0x52: cpu.d = cpu.d; break;
        case 0x53: cpu.d = cpu.e; break;
        case 0x54: cpu.d = cpu.h; break;
        case 0x55: cpu.d = cpu.l; break;
        case 0x56: cpu.d = mem_read(get_hl()); cycles = 8; break;
        case 0x57: cpu.d = cpu.a; break;
        case 0x58: cpu.e = cpu.b; break;
        case 0x59: cpu.e = cpu.c; break;
        case 0x5A: cpu.e = cpu.d; break;
        case 0x5B: cpu.e = cpu.e; break;
        case 0x5C: cpu.e = cpu.h; break;
        case 0x5D: cpu.e = cpu.l; break;
        case 0x5E: cpu.e = mem_read(get_hl()); cycles = 8; break;
        case 0x5F: cpu.e = cpu.a; break;
        case 0x60: cpu.h = cpu.b; break;
        case 0x61: cpu.h = cpu.c; break;
        case 0x62: cpu.h = cpu.d; break;
        case 0x63: cpu.h = cpu.e; break;
        case 0x64: cpu.h = cpu.h; break;
        case 0x65: cpu.h = cpu.l; break;
        case 0x66: cpu.h = mem_read(get_hl()); cycles = 8; break;
        case 0x67: cpu.h = cpu.a; break;
        case 0x68: cpu.l = cpu.b; break;
        case 0x69: cpu.l = cpu.c; break;
        case 0x6A: cpu.l = cpu.d; break;
        case 0x6B: cpu.l = cpu.e; break;
        case 0x6C: cpu.l = cpu.h; break;
        case 0x6D: cpu.l = cpu.l; break;
        case 0x6E: cpu.l = mem_read(get_hl()); cycles = 8; break;
        case 0x6F: cpu.l = cpu.a; break;
        case 0x70: mem_write(get_hl(), cpu.b); cycles = 8; break;
        case 0x71: mem_write(get_hl(), cpu.c); cycles = 8; break;
        case 0x72: mem_write(get_hl(), cpu.d); cycles = 8; break;
        case 0x73: mem_write(get_hl(), cpu.e); cycles = 8; break;
        case 0x74: mem_write(get_hl(), cpu.h); cycles = 8; break;
        case 0x75: mem_write(get_hl(), cpu.l); cycles = 8; break;
        case 0x77: mem_write(get_hl(), cpu.a); cycles = 8; break;
        case 0x0A: cpu.a = mem_read(get_bc()); cycles = 8; break;
        case 0x1A: cpu.a = mem_read(get_de()); cycles = 8; break;
        case 0x7F: cpu.a = cpu.a; break;
        case 0x78: cpu.a = cpu.b; break;
        case 0x79: cpu.a = cpu.c; break;
        case 0x7A: cpu.a = cpu.d; break;
        case 0x7B: cpu.a = cpu.e; break;
        case 0x7C: cpu.a = cpu.h; break;
        case 0x7D: cpu.a = cpu.l; break;
        case 0x7E: cpu.a = mem_read(get_hl()); cycles = 8; break;

        /* LD immediate */
        case 0x06: cpu.b = fetch8(); cycles = 8; break;
        case 0x0E: cpu.c = fetch8(); cycles = 8; break;
        case 0x16: cpu.d = fetch8(); cycles = 8; break;
        case 0x1E: cpu.e = fetch8(); cycles = 8; break;
        case 0x26: cpu.h = fetch8(); cycles = 8; break;
        case 0x2E: cpu.l = fetch8(); cycles = 8; break;
        case 0x3E: cpu.a = fetch8(); cycles = 8; break;

        /* LD (addr),A / LD A,(addr) */
        case 0xEA: { uint16_t addr = fetch16(); mem_write(addr, cpu.a); cycles = 16; } break;
        case 0xFA: { uint16_t addr = fetch16(); cpu.a = mem_read(addr); cycles = 16; } break;

        /* LD (C),A / LD A,(C) */
        case 0xE2: mem_write(0xFF00 | cpu.c, cpu.a); cycles = 8; break;
        case 0xF2: cpu.a = mem_read(0xFF00 | cpu.c); cycles = 8; break;

        /* LD (HLI/A) etc. */
        case 0x22: mem_write(get_hl(), cpu.a); set_hl(get_hl() + 1); cycles = 8; break;
        case 0x32: mem_write(get_hl(), cpu.a); set_hl(get_hl() - 1); cycles = 8; break;
        case 0x2A: cpu.a = mem_read(get_hl()); set_hl(get_hl() + 1); cycles = 8; break;
        case 0x3A: cpu.a = mem_read(get_hl()); set_hl(get_hl() - 1); cycles = 8; break;

        /* ---------- 16-bit loads ---------- */
        case 0x01: set_bc(fetch16()); cycles = 12; break;
        case 0x11: set_de(fetch16()); cycles = 12; break;
        case 0x21: set_hl(fetch16()); cycles = 12; break;
        case 0x31: cpu.sp = fetch16(); cycles = 12; break;

        /* LD SP,HL */
        case 0xF9: cpu.sp = get_hl(); cycles = 8; break;

        /* PUSH */
        case 0xC5: cpu.sp -= 2; mem_write(cpu.sp, cpu.c); mem_write(cpu.sp+1, cpu.b); cycles = 16; break;
        case 0xD5: cpu.sp -= 2; mem_write(cpu.sp, cpu.e); mem_write(cpu.sp+1, cpu.d); cycles = 16; break;
        case 0xE5: cpu.sp -= 2; mem_write(cpu.sp, cpu.l); mem_write(cpu.sp+1, cpu.h); cycles = 16; break;
        case 0xF5: cpu.sp -= 2; mem_write(cpu.sp, cpu.f); mem_write(cpu.sp+1, cpu.a); cycles = 16; break;

        /* POP */
        case 0xC1: cpu.c = mem_read(cpu.sp); cpu.b = mem_read(cpu.sp+1); cpu.sp += 2; cycles = 12; break;
        case 0xD1: cpu.e = mem_read(cpu.sp); cpu.d = mem_read(cpu.sp+1); cpu.sp += 2; cycles = 12; break;
        case 0xE1: cpu.l = mem_read(cpu.sp); cpu.h = mem_read(cpu.sp+1); cpu.sp += 2; cycles = 12; break;
        case 0xF1: cpu.f = mem_read(cpu.sp); cpu.a = mem_read(cpu.sp+1); cpu.sp += 2; cycles = 12; break;

        /* ---------- 8-bit ALU ---------- */
        /* ADD A,r */
        case 0x87: tmp8 = cpu.a; cpu.a += cpu.a; cycles = 4; goto add_flags;
        case 0x80: tmp8 = cpu.b; cpu.a += cpu.b; cycles = 4; goto add_flags;
        case 0x81: tmp8 = cpu.c; cpu.a += cpu.c; cycles = 4; goto add_flags;
        case 0x82: tmp8 = cpu.d; cpu.a += cpu.d; cycles = 4; goto add_flags;
        case 0x83: tmp8 = cpu.e; cpu.a += cpu.e; cycles = 4; goto add_flags;
        case 0x84: tmp8 = cpu.h; cpu.a += cpu.h; cycles = 4; goto add_flags;
        case 0x85: tmp8 = cpu.l; cpu.a += cpu.l; cycles = 4; goto add_flags;
        case 0x86: tmp8 = mem_read(get_hl()); cpu.a += tmp8; cycles = 8; goto add_flags;
        case 0xC6: tmp8 = fetch8(); cpu.a += tmp8; cycles = 8; goto add_flags;
        add_flags:
            cpu.f = 0;
            if ((cpu.a & 0xFF) == 0) cpu.f |= FLAG_Z;
            if ((tmp8 & 0x0F) + ((cpu.a - tmp8) & 0x0F) > 0x0F) cpu.f |= FLAG_H;
            if ((tmp8) + (cpu.a - tmp8) > 0xFF) cpu.f |= FLAG_C;
            break;

        /* ADC A,r */
        case 0x8F: tmp8 = cpu.a; goto adc;  // ADC A,A
        case 0x88: tmp8 = cpu.b; goto adc;
        case 0x89: tmp8 = cpu.c; goto adc;
        case 0x8A: tmp8 = cpu.d; goto adc;
        case 0x8B: tmp8 = cpu.e; goto adc;
        case 0x8C: tmp8 = cpu.h; goto adc;
        case 0x8D: tmp8 = cpu.l; goto adc;
        case 0x8E: tmp8 = mem_read(get_hl()); cycles = 8; goto adc;
        case 0xCE: tmp8 = fetch8(); cycles = 8; goto adc;
        adc: {
            uint8_t carry = (cpu.f & FLAG_C) ? 1 : 0;
            uint16_t res = cpu.a + tmp8 + carry;
            cpu.f = 0;
            if ((res & 0xFF) == 0) cpu.f |= FLAG_Z;
            if ((cpu.a & 0x0F) + (tmp8 & 0x0F) + carry > 0x0F) cpu.f |= FLAG_H;
            if (res > 0xFF) cpu.f |= FLAG_C;
            cpu.a = res & 0xFF;
        } break;

        /* SUB A,r */
        case 0x97: tmp8 = cpu.a; cpu.a -= cpu.a; cycles = 4; goto sub_flags;
        case 0x90: tmp8 = cpu.b; cpu.a -= cpu.b; cycles = 4; goto sub_flags;
        case 0x91: tmp8 = cpu.c; cpu.a -= cpu.c; cycles = 4; goto sub_flags;
        case 0x92: tmp8 = cpu.d; cpu.a -= cpu.d; cycles = 4; goto sub_flags;
        case 0x93: tmp8 = cpu.e; cpu.a -= cpu.e; cycles = 4; goto sub_flags;
        case 0x94: tmp8 = cpu.h; cpu.a -= cpu.h; cycles = 4; goto sub_flags;
        case 0x95: tmp8 = cpu.l; cpu.a -= cpu.l; cycles = 4; goto sub_flags;
        case 0x96: tmp8 = mem_read(get_hl()); cpu.a -= tmp8; cycles = 8; goto sub_flags;
        case 0xD6: tmp8 = fetch8(); cpu.a -= tmp8; cycles = 8; goto sub_flags;
        sub_flags:
            cpu.f = FLAG_N;
            if ((cpu.a & 0xFF) == 0) cpu.f |= FLAG_Z;
            if ((tmp8 & 0x0F) > ((cpu.a + tmp8) & 0x0F)) cpu.f |= FLAG_H;
            if ((tmp8) > (cpu.a + tmp8)) cpu.f |= FLAG_C;
            break;

        /* SBC A,r */
        case 0x9F: tmp8 = cpu.a; goto sbc;
        case 0x98: tmp8 = cpu.b; goto sbc;
        case 0x99: tmp8 = cpu.c; goto sbc;
        case 0x9A: tmp8 = cpu.d; goto sbc;
        case 0x9B: tmp8 = cpu.e; goto sbc;
        case 0x9C: tmp8 = cpu.h; goto sbc;
        case 0x9D: tmp8 = cpu.l; goto sbc;
        case 0x9E: tmp8 = mem_read(get_hl()); cycles = 8; goto sbc;
        case 0xDE: tmp8 = fetch8(); cycles = 8; goto sbc;
        sbc: {
            uint8_t carry = (cpu.f & FLAG_C) ? 1 : 0;
            uint16_t res = cpu.a - tmp8 - carry;
            cpu.f = FLAG_N;
            if ((res & 0xFF) == 0) cpu.f |= FLAG_Z;
            if ((cpu.a & 0x0F) < (tmp8 & 0x0F) + carry) cpu.f |= FLAG_H;
            if (cpu.a < tmp8 + carry) cpu.f |= FLAG_C;
            cpu.a = res & 0xFF;
        } break;

        /* AND A,r */
        case 0xA7: cpu.a &= cpu.a; cycles = 4; goto and_flags;
        case 0xA0: cpu.a &= cpu.b; cycles = 4; goto and_flags;
        case 0xA1: cpu.a &= cpu.c; cycles = 4; goto and_flags;
        case 0xA2: cpu.a &= cpu.d; cycles = 4; goto and_flags;
        case 0xA3: cpu.a &= cpu.e; cycles = 4; goto and_flags;
        case 0xA4: cpu.a &= cpu.h; cycles = 4; goto and_flags;
        case 0xA5: cpu.a &= cpu.l; cycles = 4; goto and_flags;
        case 0xA6: cpu.a &= mem_read(get_hl()); cycles = 8; goto and_flags;
        case 0xE6: cpu.a &= fetch8(); cycles = 8; goto and_flags;
        and_flags:
            cpu.f = FLAG_H; /* H is set after AND */
            if ((cpu.a & 0xFF) == 0) cpu.f |= FLAG_Z;
            break;

        /* OR A,r */
        case 0xB7: cpu.a |= cpu.a; cycles = 4; goto or_flags;
        case 0xB0: cpu.a |= cpu.b; cycles = 4; goto or_flags;
        case 0xB1: cpu.a |= cpu.c; cycles = 4; goto or_flags;
        case 0xB2: cpu.a |= cpu.d; cycles = 4; goto or_flags;
        case 0xB3: cpu.a |= cpu.e; cycles = 4; goto or_flags;
        case 0xB4: cpu.a |= cpu.h; cycles = 4; goto or_flags;
        case 0xB5: cpu.a |= cpu.l; cycles = 4; goto or_flags;
        case 0xB6: cpu.a |= mem_read(get_hl()); cycles = 8; goto or_flags;
        case 0xF6: cpu.a |= fetch8(); cycles = 8; goto or_flags;
        or_flags:
            cpu.f = 0;
            if ((cpu.a & 0xFF) == 0) cpu.f |= FLAG_Z;
            break;

        /* XOR A,r */
        case 0xAF: cpu.a ^= cpu.a; cycles = 4; goto xor_flags;
        case 0xA8: cpu.a ^= cpu.b; cycles = 4; goto xor_flags;
        case 0xA9: cpu.a ^= cpu.c; cycles = 4; goto xor_flags;
        case 0xAA: cpu.a ^= cpu.d; cycles = 4; goto xor_flags;
        case 0xAB: cpu.a ^= cpu.e; cycles = 4; goto xor_flags;
        case 0xAC: cpu.a ^= cpu.h; cycles = 4; goto xor_flags;
        case 0xAD: cpu.a ^= cpu.l; cycles = 4; goto xor_flags;
        case 0xAE: cpu.a ^= mem_read(get_hl()); cycles = 8; goto xor_flags;
        case 0xEE: cpu.a ^= fetch8(); cycles = 8; goto xor_flags;
        xor_flags:
            cpu.f = 0;
            if ((cpu.a & 0xFF) == 0) cpu.f |= FLAG_Z;
            break;

        /* CP A,r (compare) */
        case 0xBF: tmp8 = cpu.a; goto cp_flags;
        case 0xB8: tmp8 = cpu.b; goto cp_flags;
        case 0xB9: tmp8 = cpu.c; goto cp_flags;
        case 0xBA: tmp8 = cpu.d; goto cp_flags;
        case 0xBB: tmp8 = cpu.e; goto cp_flags;
        case 0xBC: tmp8 = cpu.h; goto cp_flags;
        case 0xBD: tmp8 = cpu.l; goto cp_flags;
        case 0xBE: tmp8 = mem_read(get_hl()); cycles = 8; goto cp_flags;
        case 0xFE: tmp8 = fetch8(); cycles = 8; goto cp_flags;
        cp_flags:
            {
                uint16_t result = cpu.a - tmp8;
                cpu.f = FLAG_N;
                if ((result & 0xFF) == 0) cpu.f |= FLAG_Z;
                if ((tmp8 & 0x0F) > (cpu.a & 0x0F)) cpu.f |= FLAG_H;
                if (tmp8 > cpu.a) cpu.f |= FLAG_C;
            }
            break;

        /* INC r */
        case 0x04: cpu.b++; tmp8 = cpu.b; cycles = 4; goto inc_flags;
        case 0x0C: cpu.c++; tmp8 = cpu.c; cycles = 4; goto inc_flags;
        case 0x14: cpu.d++; tmp8 = cpu.d; cycles = 4; goto inc_flags;
        case 0x1C: cpu.e++; tmp8 = cpu.e; cycles = 4; goto inc_flags;
        case 0x24: cpu.h++; tmp8 = cpu.h; cycles = 4; goto inc_flags;
        case 0x2C: cpu.l++; tmp8 = cpu.l; cycles = 4; goto inc_flags;
        case 0x3C: cpu.a++; tmp8 = cpu.a; cycles = 4; goto inc_flags;
        case 0x34: tmp8 = mem_read(get_hl()); tmp8++; mem_write(get_hl(), tmp8); cycles = 12; goto inc_flags;
        inc_flags:
            cpu.f &= 0x10; /* keep carry, clear others */
            if ((tmp8 & 0xFF) == 0) cpu.f |= FLAG_Z;
            if ((tmp8 & 0x0F) == 0) cpu.f |= FLAG_H;
            break;

        /* DEC r */
        case 0x05: cpu.b--; tmp8 = cpu.b; cycles = 4; goto dec_flags;
        case 0x0D: cpu.c--; tmp8 = cpu.c; cycles = 4; goto dec_flags;
        case 0x15: cpu.d--; tmp8 = cpu.d; cycles = 4; goto dec_flags;
        case 0x1D: cpu.e--; tmp8 = cpu.e; cycles = 4; goto dec_flags;
        case 0x25: cpu.h--; tmp8 = cpu.h; cycles = 4; goto dec_flags;
        case 0x2D: cpu.l--; tmp8 = cpu.l; cycles = 4; goto dec_flags;
        case 0x3D: cpu.a--; tmp8 = cpu.a; cycles = 4; goto dec_flags;
        case 0x35: tmp8 = mem_read(get_hl()); tmp8--; mem_write(get_hl(), tmp8); cycles = 12; goto dec_flags;
        dec_flags:
            cpu.f &= 0x10;
            cpu.f |= FLAG_N;
            if ((tmp8 & 0xFF) == 0) cpu.f |= FLAG_Z;
            if ((tmp8 & 0x0F) == 0x0F) cpu.f |= FLAG_H;
            break;

        /* ---------- 16-bit ALU ---------- */
        case 0x09: /* ADD HL,BC */
            tmp16 = get_hl() + get_bc();
            cpu.f &= 0x80; /* keep Z? Actually Z not affected */
            if ((get_hl() & 0x0FFF) + (get_bc() & 0x0FFF) > 0x0FFF) cpu.f |= FLAG_H;
            if ((uint32_t)get_hl() + get_bc() > 0xFFFF) cpu.f |= FLAG_C;
            set_hl(tmp16);
            cycles = 8;
            break;
        case 0x19: /* ADD HL,DE */
            tmp16 = get_hl() + get_de();
            cpu.f &= 0x80;
            if ((get_hl() & 0x0FFF) + (get_de() & 0x0FFF) > 0x0FFF) cpu.f |= FLAG_H;
            if ((uint32_t)get_hl() + get_de() > 0xFFFF) cpu.f |= FLAG_C;
            set_hl(tmp16);
            cycles = 8;
            break;
        case 0x29: /* ADD HL,HL */
            tmp16 = get_hl() + get_hl();
            cpu.f &= 0x80;
            if ((get_hl() & 0x0FFF) * 2 > 0x0FFF) cpu.f |= FLAG_H;
            if ((uint32_t)get_hl() * 2 > 0xFFFF) cpu.f |= FLAG_C;
            set_hl(tmp16);
            cycles = 8;
            break;
        case 0x39: /* ADD HL,SP */
            tmp16 = get_hl() + cpu.sp;
            cpu.f &= 0x80;
            if ((get_hl() & 0x0FFF) + (cpu.sp & 0x0FFF) > 0x0FFF) cpu.f |= FLAG_H;
            if ((uint32_t)get_hl() + cpu.sp > 0xFFFF) cpu.f |= FLAG_C;
            set_hl(tmp16);
            cycles = 8;
            break;

        /* ---------- 16-bit INC/DEC ---------- */
        case 0x03: set_bc(get_bc() + 1); cycles = 8; break; // INC BC
        case 0x13: set_de(get_de() + 1); cycles = 8; break; // INC DE
        case 0x23: set_hl(get_hl() + 1); cycles = 8; break; // INC HL
        case 0x33: cpu.sp++; cycles = 8; break;             // INC SP
        case 0x0B: set_bc(get_bc() - 1); cycles = 8; break; // DEC BC
        case 0x1B: set_de(get_de() - 1); cycles = 8; break; // DEC DE
        case 0x2B: set_hl(get_hl() - 1); cycles = 8; break; // DEC HL
        case 0x3B: cpu.sp--; cycles = 8; break;             // DEC SP

        /* ADD SP,n */
        case 0xE8: {
            int8_t n = (int8_t)fetch8();
            uint16_t res = cpu.sp + n;
            cpu.f = 0;
            if ((cpu.sp & 0xFF) + (n & 0xFF) > 0xFF) cpu.f |= FLAG_C;
            if ((cpu.sp & 0x0F) + (n & 0x0F) > 0x0F) cpu.f |= FLAG_H;
            cpu.sp = res;
            cycles = 16;
        } break;

        /* LD HL,SP+n */
        case 0xF8: {
            int8_t n = (int8_t)fetch8();
            uint16_t res = cpu.sp + n;
            cpu.f = 0;
            if ((cpu.sp & 0xFF) + (n & 0xFF) > 0xFF) cpu.f |= FLAG_C;
            if ((cpu.sp & 0x0F) + (n & 0x0F) > 0x0F) cpu.f |= FLAG_H;
            set_hl(res);
            cycles = 12;
        } break;

        /* ---------- Rotates & misc ---------- */
        case 0x07: /* RLCA */
            cpu.a = (cpu.a << 1) | (cpu.a >> 7);
            cpu.f = (cpu.a & 1) ? FLAG_C : 0;
            cycles = 4;
            break;
        case 0x0F: /* RRCA */
            cpu.f = (cpu.a & 1) ? FLAG_C : 0;
            cpu.a = (cpu.a >> 1) | (cpu.a << 7);
            cycles = 4;
            break;
        case 0x17: /* RLA */
            {
                uint8_t old_c = (cpu.f & FLAG_C) ? 1 : 0;
                uint8_t new_c = (cpu.a & 0x80) ? 1 : 0;
                cpu.a = (cpu.a << 1) | old_c;
                cpu.f = new_c ? FLAG_C : 0;
                cycles = 4;
            }
            break;
        case 0x1F: /* RRA */
            {
                uint8_t old_c = (cpu.f & FLAG_C) ? 1 : 0;
                uint8_t new_c = (cpu.a & 1) ? 1 : 0;
                cpu.a = (cpu.a >> 1) | (old_c << 7);
                cpu.f = new_c ? FLAG_C : 0;
                cycles = 4;
            }
            break;

        /* ---------- DAA ---------- */
        case 0x27: {
            uint16_t a = cpu.a;
            if (!(cpu.f & FLAG_N)) {
                if ((cpu.f & FLAG_H) || (a & 0x0F) > 9) a += 6;
                if ((cpu.f & FLAG_C) || a > 0x9F) a += 0x60;
            } else {
                if (cpu.f & FLAG_H) a = (a - 6) & 0xFF;
                if (cpu.f & FLAG_C) a -= 0x60;
            }
            cpu.f &= ~(FLAG_H | FLAG_Z);
            if (a & 0x100) cpu.f |= FLAG_C;
            cpu.a = a & 0xFF;
            if (cpu.a == 0) cpu.f |= FLAG_Z;
            cycles = 4;
        } break;

        /* ---------- CPL ---------- */
        case 0x2F:
            cpu.a = ~cpu.a;
            cpu.f |= FLAG_N | FLAG_H;
            cycles = 4;
            break;

        /* ---------- SCF ---------- */
        case 0x37:
            cpu.f |= FLAG_C;
            cpu.f &= ~(FLAG_N | FLAG_H);
            cycles = 4;
            break;

        /* ---------- CCF ---------- */
        case 0x3F:
            cpu.f ^= FLAG_C;
            cpu.f &= ~(FLAG_N | FLAG_H);
            cycles = 4;
            break;

        /* ---------- Jumps ---------- */
        case 0xC3: cpu.pc = fetch16(); cycles = 16; break; /* JP nn */
        case 0xC2: /* JP NZ,nn */
            tmp16 = fetch16();
            if (!(cpu.f & FLAG_Z)) cpu.pc = tmp16;
            cycles = 16;
            break;
        case 0xCA: /* JP Z,nn */
            tmp16 = fetch16();
            if (cpu.f & FLAG_Z) cpu.pc = tmp16;
            cycles = 16;
            break;
        case 0xD2: /* JP NC,nn */
            tmp16 = fetch16();
            if (!(cpu.f & FLAG_C)) cpu.pc = tmp16;
            cycles = 16;
            break;
        case 0xDA: /* JP C,nn */
            tmp16 = fetch16();
            if (cpu.f & FLAG_C) cpu.pc = tmp16;
            cycles = 16;
            break;
        case 0x18: /* JR n */
            tmp8 = (int8_t)fetch8();
            cpu.pc += tmp8;
            cycles = 12;
            break;
        case 0x20: /* JR NZ,n */
            tmp8 = (int8_t)fetch8();
            if (!(cpu.f & FLAG_Z)) { cpu.pc += tmp8; cycles = 12; }
            else cycles = 8;
            break;
        case 0x28: /* JR Z,n */
            tmp8 = (int8_t)fetch8();
            if (cpu.f & FLAG_Z) { cpu.pc += tmp8; cycles = 12; }
            else cycles = 8;
            break;
        case 0x30: /* JR NC,n */
            tmp8 = (int8_t)fetch8();
            if (!(cpu.f & FLAG_C)) { cpu.pc += tmp8; cycles = 12; }
            else cycles = 8;
            break;
        case 0x38: /* JR C,n */
            tmp8 = (int8_t)fetch8();
            if (cpu.f & FLAG_C) { cpu.pc += tmp8; cycles = 12; }
            else cycles = 8;
            break;

        /* ---------- Calls & Returns ---------- */
        case 0xCD: /* CALL nn */
            tmp16 = fetch16();
            cpu.sp -= 2;
            mem_write(cpu.sp, cpu.pc & 0xFF);
            mem_write(cpu.sp+1, cpu.pc >> 8);
            cpu.pc = tmp16;
            cycles = 24;
            break;
        case 0xC4: /* CALL NZ,nn */
            tmp16 = fetch16();
            if (!(cpu.f & FLAG_Z)) {
                cpu.sp -= 2;
                mem_write(cpu.sp, cpu.pc & 0xFF);
                mem_write(cpu.sp+1, cpu.pc >> 8);
                cpu.pc = tmp16;
                cycles = 24;
            } else cycles = 12;
            break;
        case 0xCC: /* CALL Z,nn */
            tmp16 = fetch16();
            if (cpu.f & FLAG_Z) {
                cpu.sp -= 2;
                mem_write(cpu.sp, cpu.pc & 0xFF);
                mem_write(cpu.sp+1, cpu.pc >> 8);
                cpu.pc = tmp16;
                cycles = 24;
            } else cycles = 12;
            break;
        case 0xD4: /* CALL NC,nn */
            tmp16 = fetch16();
            if (!(cpu.f & FLAG_C)) {
                cpu.sp -= 2;
                mem_write(cpu.sp, cpu.pc & 0xFF);
                mem_write(cpu.sp+1, cpu.pc >> 8);
                cpu.pc = tmp16;
                cycles = 24;
            } else cycles = 12;
            break;
        case 0xDC: /* CALL C,nn */
            tmp16 = fetch16();
            if (cpu.f & FLAG_C) {
                cpu.sp -= 2;
                mem_write(cpu.sp, cpu.pc & 0xFF);
                mem_write(cpu.sp+1, cpu.pc >> 8);
                cpu.pc = tmp16;
                cycles = 24;
            } else cycles = 12;
            break;
        case 0xC9: /* RET */
            cpu.pc = mem_read(cpu.sp) | (mem_read(cpu.sp+1) << 8);
            cpu.sp += 2;
            cycles = 16;
            break;
        case 0xC0: /* RET NZ */
            if (!(cpu.f & FLAG_Z)) {
                cpu.pc = mem_read(cpu.sp) | (mem_read(cpu.sp+1) << 8);
                cpu.sp += 2;
                cycles = 20;
            } else cycles = 8;
            break;
        case 0xC8: /* RET Z */
            if (cpu.f & FLAG_Z) {
                cpu.pc = mem_read(cpu.sp) | (mem_read(cpu.sp+1) << 8);
                cpu.sp += 2;
                cycles = 20;
            } else cycles = 8;
            break;
        case 0xD0: /* RET NC */
            if (!(cpu.f & FLAG_C)) {
                cpu.pc = mem_read(cpu.sp) | (mem_read(cpu.sp+1) << 8);
                cpu.sp += 2;
                cycles = 20;
            } else cycles = 8;
            break;
        case 0xD8: /* RET C */
            if (cpu.f & FLAG_C) {
                cpu.pc = mem_read(cpu.sp) | (mem_read(cpu.sp+1) << 8);
                cpu.sp += 2;
                cycles = 20;
            } else cycles = 8;
            break;
        case 0xD9: /* RETI */
            cpu.pc = mem_read(cpu.sp) | (mem_read(cpu.sp+1) << 8);
            cpu.sp += 2;
            cpu.ime = 1;
            cycles = 16;
            break;

        /* ---------- RST ---------- */
        case 0xC7: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x00; cycles = 16; break;
        case 0xCF: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x08; cycles = 16; break;
        case 0xD7: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x10; cycles = 16; break;
        case 0xDF: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x18; cycles = 16; break;
        case 0xE7: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x20; cycles = 16; break;
        case 0xEF: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x28; cycles = 16; break;
        case 0xF7: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x30; cycles = 16; break;
        case 0xFF: cpu.sp -= 2; mem_write(cpu.sp, cpu.pc & 0xFF); mem_write(cpu.sp+1, cpu.pc>>8); cpu.pc = 0x38; cycles = 16; break;

        /* ---------- Interrupt flags / misc ---------- */
        case 0xF3: /* DI */
            cpu.ime = 0;
            cycles = 4;
            break;
        case 0xFB: /* EI */
            cpu.ime = 1;
            cycles = 4;
            break;
        case 0x76: /* HALT */
            cpu.halt = 1;
            cycles = 4;
            break;
        case 0x00: /* NOP */ break;
        case 0x10: /* STOP */ /* treat as NOP */ break;

        /* ---------- LD (nn),SP (0x08) ---------- */
        case 0x08: {
            uint16_t addr = fetch16();
            mem_write(addr, cpu.sp & 0xFF);
            mem_write(addr + 1, cpu.sp >> 8);
            cycles = 20;
        } break;

        /* ---------- 0xCB prefix – handle all extended opcodes ---------- */
        case 0xCB: {
            uint8_t cb_op = fetch8();
            uint16_t hl = get_hl();
            uint8_t *regs[8] = { &cpu.b, &cpu.c, &cpu.d, &cpu.e, &cpu.h, &cpu.l, NULL, &cpu.a };
            uint8_t val, res;
            int bit;

            // Helper to read operand (register or (HL))
            uint8_t read_operand(int reg) {
                if (reg == 6) return mem_read(hl);
                else return *regs[reg];
            }

            // Helper to write result
            void write_operand(int reg, uint8_t v) {
                if (reg == 6) mem_write(hl, v);
                else *regs[reg] = v;
            }

            int reg = cb_op & 0x07;
            int op_type = cb_op >> 6;        // 0,1,2,3 for the four groups
            int bit_num = (cb_op >> 3) & 7;

            switch (op_type) {
                case 0: // Rotates and shifts (0x00-0x3F)
                    val = read_operand(reg);
                    switch ((cb_op >> 3) & 7) { // lower 3 bits of high nibble
                        case 0: // RLC
                            cpu.f = (val & 0x80) ? FLAG_C : 0;
                            res = (val << 1) | (val >> 7);
                            if (res == 0) cpu.f |= FLAG_Z;
                            write_operand(reg, res);
                            break;
                        case 1: // RRC
                            cpu.f = (val & 0x01) ? FLAG_C : 0;
                            res = (val >> 1) | (val << 7);
                            if (res == 0) cpu.f |= FLAG_Z;
                            write_operand(reg, res);
                            break;
                        case 2: // RL
                            {
                                uint8_t old_c = (cpu.f & FLAG_C) ? 1 : 0;
                                cpu.f = (val & 0x80) ? FLAG_C : 0;
                                res = (val << 1) | old_c;
                                if (res == 0) cpu.f |= FLAG_Z;
                                write_operand(reg, res);
                            }
                            break;
                        case 3: // RR
                            {
                                uint8_t old_c = (cpu.f & FLAG_C) ? 1 : 0;
                                cpu.f = (val & 0x01) ? FLAG_C : 0;
                                res = (val >> 1) | (old_c << 7);
                                if (res == 0) cpu.f |= FLAG_Z;
                                write_operand(reg, res);
                            }
                            break;
                        case 4: // SLA
                            cpu.f = (val & 0x80) ? FLAG_C : 0;
                            res = val << 1;
                            if (res == 0) cpu.f |= FLAG_Z;
                            write_operand(reg, res);
                            break;
                        case 5: // SRA
                            cpu.f = (val & 0x01) ? FLAG_C : 0;
                            res = (val >> 1) | (val & 0x80); // keep MSB
                            if (res == 0) cpu.f |= FLAG_Z;
                            write_operand(reg, res);
                            break;
                        case 6: // SWAP
                            res = ((val & 0x0F) << 4) | ((val >> 4) & 0x0F);
                            cpu.f = (res == 0) ? FLAG_Z : 0;
                            write_operand(reg, res);
                            break;
                        case 7: // SRL
                            cpu.f = (val & 0x01) ? FLAG_C : 0;
                            res = val >> 1;
                            if (res == 0) cpu.f |= FLAG_Z;
                            write_operand(reg, res);
                            break;
                    }
                    cycles = (reg == 6) ? 16 : 8;
                    break;

                case 1: // BIT n,r (0x40-0x7F)
                    val = read_operand(reg);
                    cpu.f &= ~(FLAG_Z | FLAG_N);
                    cpu.f |= FLAG_H;  // H is always set for BIT
                    if (!(val & (1 << bit_num))) cpu.f |= FLAG_Z;
                    cycles = (reg == 6) ? 12 : 8;
                    break;

                case 2: // RES n,r (0x80-0xBF)
                    val = read_operand(reg);
                    res = val & ~(1 << bit_num);
                    write_operand(reg, res);
                    cycles = (reg == 6) ? 16 : 8;
                    break;

                case 3: // SET n,r (0xC0-0xFF)
                    val = read_operand(reg);
                    res = val | (1 << bit_num);
                    write_operand(reg, res);
                    cycles = (reg == 6) ? 16 : 8;
                    break;
            }
            break;
        }

        default:
            printf("Unimplemented opcode: 0x%02X at PC=0x%04X\n", opcode, cpu.pc-1);
            exit(1);
    }

    cpu.cycles += cycles;
    return cycles;
}

/* -------------------------------- Interrupt Handling ---------------------- */
void check_interrupts() {
    if (!cpu.ime || cpu.halt) return;
    uint8_t req = mem_read(IF) & interrupt_enable;
    if (req == 0) return;

    // Find highest priority interrupt (bit 0 = VBlank, highest)
    int bit;
    for (bit = 0; bit < 5; bit++) {
        if (req & (1 << bit)) break;
    }
    if (bit == 5) return; // no interrupt

    cpu.halt = 0;
    cpu.ime = 0;
    // Push PC
    cpu.sp -= 2;
    mem_write(cpu.sp, cpu.pc & 0xFF);
    mem_write(cpu.sp + 1, cpu.pc >> 8);
    // Jump to interrupt vector
    cpu.pc = 0x40 + bit * 8;
    // Clear the interrupt flag
    mem_write(IF, mem_read(IF) & ~(1 << bit));
    cpu.cycles += 20; // interrupt takes 5 cycles? Actually 5? We'll add 20 for safety
}

/* -------------------------------- PPU (background only) ------------------ */
void render_frame(SDL_Renderer *renderer, SDL_Texture *texture) {
    uint32_t pixels[SCREEN_W * SCREEN_H];
    uint8_t lcdc = mem_read(LCDC);

    if (!(lcdc & 0x80)) { /* LCD off? */
        SDL_RenderClear(renderer);
        SDL_RenderPresent(renderer);
        return;
    }

    /* Background tile data address (0x8000 or 0x8800) */
    uint16_t tile_data_base = (lcdc & 0x10) ? 0x8000 : 0x8800;
    /* Background map address (0x9800 or 0x9C00) */
    uint16_t bg_map_base = (lcdc & 0x08) ? 0x9C00 : 0x9800;

    uint8_t scx = mem_read(SCX);
    uint8_t scy = mem_read(SCY);
    uint8_t bgp = mem_read(BGP); /* palette: bits 7-6,5-4,3-2,1-0 for shades 3,2,1,0 */

    for (int y = 0; y < SCREEN_H; y++) {
        int map_y = (y + scy) & 0xFF; /* scroll wraps at 256 */
        int tile_row = map_y / 8;

        for (int x = 0; x < SCREEN_W; x++) {
            int map_x = (x + scx) & 0xFF;
            int tile_col = map_x / 8;

            /* Get tile index from background map */
            uint16_t map_addr = bg_map_base + tile_row * 32 + tile_col;
            uint8_t tile_index = mem_read(map_addr);

            /* Determine tile data address */
            uint16_t tile_addr;
            if (tile_data_base == 0x8000) {
                tile_addr = 0x8000 + tile_index * 16;
            } else {
                /* 0x8800: signed addressing */
                tile_addr = 0x9000 + (int8_t)tile_index * 16;
            }

            /* Find pixel inside tile */
            int tile_y = (map_y % 8);
            int tile_x = (map_x % 8);
            uint8_t tile_low = mem_read(tile_addr + tile_y * 2);
            uint8_t tile_high = mem_read(tile_addr + tile_y * 2 + 1);

            /* Pixel color number (0-3) */
            int bit = 7 - tile_x;
            uint8_t color_num = ((tile_low >> bit) & 1) | (((tile_high >> bit) & 1) << 1);

            /* Map to grayscale via BGP */
            uint8_t shade = (bgp >> (color_num * 2)) & 3;
            uint8_t grey = (3 - shade) * 85; // 0->255, 1->170, 2->85, 3->0
            pixels[y * SCREEN_W + x] = (grey << 16) | (grey << 8) | grey;
        }
    }

    SDL_UpdateTexture(texture, NULL, pixels, SCREEN_W * sizeof(uint32_t));
    SDL_RenderClear(renderer);
    SDL_RenderCopy(renderer, texture, NULL, NULL);
    SDL_RenderPresent(renderer);
}

/* -------------------------------- Joypad ---------------------------------- */
void update_joypad(const uint8_t *keys) {
    uint8_t p1 = mem_read(P1) & 0xF0; /* keep upper bits */
    uint8_t column = (p1 >> 4) & 0x03; /* bits 4 and 5 select direction/action */

    if (!(column & 0x01)) { /* direction selected */
        p1 |= 0x0F;
        if (keys[SDL_SCANCODE_RIGHT]) p1 &= ~0x01;
        if (keys[SDL_SCANCODE_LEFT])  p1 &= ~0x02;
        if (keys[SDL_SCANCODE_UP])    p1 &= ~0x04;
        if (keys[SDL_SCANCODE_DOWN])  p1 &= ~0x08;
    }
    if (!(column & 0x02)) { /* action selected */
        p1 |= 0x0F;
        if (keys[SDL_SCANCODE_Z]) p1 &= ~0x01; /* A */
        if (keys[SDL_SCANCODE_X]) p1 &= ~0x02; /* B */
        if (keys[SDL_SCANCODE_BACKSPACE]) p1 &= ~0x04; /* Select */
        if (keys[SDL_SCANCODE_RETURN])    p1 &= ~0x08; /* Start */
    }
    mem_write(P1, p1);
}

/* -------------------------------- Main ------------------------------------ */
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <rom.gb>\n", argv[0]);
        return 1;
    }

    /* Load ROM */
    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }
    fread(rom, 1, sizeof(rom), f);
    fclose(f);

    /* Initialize CPU */
    cpu.pc = 0x0100;
    cpu.sp = 0xFFFE;
    cpu.a = 0x01; cpu.f = 0xB0; /* after boot ROM */
    cpu.b = 0x00; cpu.c = 0x13;
    cpu.d = 0x00; cpu.e = 0xD8;
    cpu.h = 0x01; cpu.l = 0x4D;
    cpu.cycles = 0;
    cpu.ime = 0;
    cpu.halt = 0;

    /* Initialize I/O registers (typical startup values) */
    memset(io, 0, sizeof(io));
    io[LCDC & 0x7F] = 0x91; /* LCD on, bg on */
    io[SCY & 0x7F] = 0;
    io[SCX & 0x7F] = 0;
    io[BGP & 0x7F] = 0xFC; /* palette 11100100 -> shades 3,2,1,0 */
    io[IF & 0x7F] = 0xE1;   /* typical: no pending interrupts */
    interrupt_enable = 0;

    /* SDL initialization */
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        fprintf(stderr, "SDL init error: %s\n", SDL_GetError());
        return 1;
    }
    SDL_Window *win = SDL_CreateWindow("Game Boy Emulator", SDL_WINDOWPOS_UNDEFINED,
                                       SDL_WINDOWPOS_UNDEFINED, SCREEN_W*3, SCREEN_H*3,
                                       SDL_WINDOW_RESIZABLE);
    if (!win) {
        fprintf(stderr, "Window error: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    SDL_Renderer *renderer = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture *texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888,
                                             SDL_TEXTUREACCESS_STREAMING, SCREEN_W, SCREEN_H);
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);

    /* Main loop */
    int running = 1;
    uint64_t last_ticks = SDL_GetTicks64();

    while (running) {
        /* Input */
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) running = 0;
        }
        const uint8_t *keys = SDL_GetKeyboardState(NULL);
        update_joypad(keys);

        /* Run CPU for one frame */
        uint64_t frame_cycles = 0;
        while (frame_cycles < CYCLES_PER_FRAME) {
            frame_cycles += cpu_step();
            /* Check for interrupts after each instruction */
            check_interrupts();
        }

        /* After a frame, request VBlank interrupt (bit 0 of IF) */
        mem_write(IF, mem_read(IF) | 1);

        /* Render */
        render_frame(renderer, texture);

        /* Simple 60 FPS cap */
        uint64_t now = SDL_GetTicks64();
        if (now - last_ticks < 16) SDL_Delay(16 - (now - last_ticks));
        last_ticks = SDL_GetTicks64();
    }

    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(win);
    SDL_Quit();
    return 0;
}