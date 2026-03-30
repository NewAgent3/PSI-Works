/*
 * nes.c - Full NES Emulator
 * Supports: Mapper 0 (NROM), Mapper 1 (MMC1), Mapper 2 (UNROM), Mapper 3 (CNROM)
 * 
 * Windows Build:
 *   Install SDL2 dev headers and MinGW, then:
 *   gcc -O2 -o nes.exe nes.c -lSDL2 -lSDL2main -mwindows
 *
 * Or with MSVC + vcpkg SDL2:
 *   cl /O2 nes.c /link SDL2.lib SDL2main.lib /SUBSYSTEM:CONSOLE
 *
 * Usage: nes.exe game.nes
 *
 * Controls:
 *   Arrow Keys = D-Pad
 *   Z = A button
 *   X = B button
 *   Enter = Start
 *   Right Shift = Select
 *   Escape = Quit
 *   R = Reset
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define SDL_MAIN_HANDLED
#include <SDL2/SDL.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int8_t   s8;
typedef int16_t  s16;

/* ======================================================
   NES PALETTE (RGBA)
   ====================================================== */
static const u32 NES_PALETTE[64] = {
    0xFF545454,0xFF001E74,0xFF081090,0xFF300088,0xFF440064,0xFF5C0030,0xFF540400,0xFF3C1800,
    0xFF202A00,0xFF083A00,0xFF004000,0xFF003C00,0xFF00323C,0xFF000000,0xFF000000,0xFF000000,
    0xFF989698,0xFF084CC4,0xFF3032EC,0xFF5C1EE4,0xFF8814B0,0xFFA01464,0xFF982220,0xFF783C00,
    0xFF545A00,0xFF287200,0xFF087C00,0xFF007628,0xFF006678,0xFF000000,0xFF000000,0xFF000000,
    0xFFECEEEC,0xFF4C9AEC,0xFF787CEC,0xFFB062EC,0xFFE454EC,0xFFEC58B4,0xFFEC6A64,0xFFD48820,
    0xFFA0AA00,0xFF74C400,0xFF4CD020,0xFF38CC6C,0xFF38B4CC,0xFF3C3C3C,0xFF000000,0xFF000000,
    0xFFECEEEC,0xFFA8CCEC,0xFFBCBCEC,0xFFD4B2EC,0xFFECAEEC,0xFFECAED4,0xFFECB4B0,0xFFE4C490,
    0xFFCCD278,0xFFB4DE78,0xFFA8E290,0xFF98E2B4,0xFFA0D6E4,0xFFA0A2A0,0xFF000000,0xFF000000,
};

/* ======================================================
   CARTRIDGE
   ====================================================== */
typedef struct {
    u8 *prg;
    u8 *chr;
    u8  prg_banks;   /* 16KB banks */
    u8  chr_banks;   /* 8KB banks  */
    u8  mapper;
    u8  mirror;      /* 0=horiz 1=vert 2=single0 3=single1 4=four */
    u8  has_battery;
    u8  chr_is_ram;
    u8  chr_ram[0x2000];

    /* Mapper state */
    /* MMC1 (mapper 1) */
    u8  mmc1_shift, mmc1_count;
    u8  mmc1_ctrl, mmc1_chr0, mmc1_chr1, mmc1_prg;
    /* UNROM (mapper 2) */
    u8  unrom_bank;
    /* CNROM (mapper 3) */
    u8  cnrom_bank;
} Cart;

Cart* cart_load(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "Cannot open ROM: %s\n", path); return NULL; }

    u8 hdr[16];
    if (fread(hdr, 1, 16, f) < 16 || hdr[0]!='N'||hdr[1]!='E'||hdr[2]!='S'||hdr[3]!=0x1A) {
        fprintf(stderr, "Not a valid iNES ROM.\n"); fclose(f); return NULL;
    }

    Cart *c = (Cart*)calloc(1, sizeof(Cart));
    c->prg_banks = hdr[4];
    c->chr_banks = hdr[5];
    c->mapper    = (hdr[7] & 0xF0) | (hdr[6] >> 4);
    c->mirror    = (hdr[6] & 0x08) ? 4 : (hdr[6] & 0x01);
    c->has_battery = (hdr[6] >> 1) & 1;

    if (hdr[6] & 0x04) fseek(f, 512, SEEK_CUR); /* skip trainer */

    int prg_sz = c->prg_banks * 16384;
    int chr_sz = c->chr_banks * 8192;

    c->prg = (u8*)malloc(prg_sz);
    fread(c->prg, 1, prg_sz, f);

    if (chr_sz > 0) {
        c->chr = (u8*)malloc(chr_sz);
        fread(c->chr, 1, chr_sz, f);
        c->chr_is_ram = 0;
    } else {
        c->chr = c->chr_ram;
        c->chr_is_ram = 1;
    }
    fclose(f);

    /* Init MMC1 */
    c->mmc1_shift = 0x10;
    c->mmc1_ctrl  = 0x0C;

    fprintf(stderr, "ROM: %d PRG banks, %d CHR banks, Mapper %d, Mirror %d\n",
            c->prg_banks, c->chr_banks, c->mapper, c->mirror);
    return c;
}

/* PRG read */
u8 cart_prg_read(Cart *c, u16 addr) {
    int bank;
    switch(c->mapper) {
        case 0:
            bank = (addr >= 0xC000 && c->prg_banks == 1) ? 0 : (addr >= 0xC000 ? 1 : 0);
            if (c->prg_banks == 1) bank = 0;
            else bank = (addr < 0xC000) ? 0 : 1;
            return c->prg[(bank * 16384) + (addr & 0x3FFF)];
        case 1: { /* MMC1 */
            int prg_mode = (c->mmc1_ctrl >> 2) & 3;
            int p = c->mmc1_prg & 0x0F;
            if (addr < 0xC000) {
                if      (prg_mode == 2) bank = 0;
                else if (prg_mode == 3) bank = p;
                else                    bank = p & ~1;
            } else {
                if      (prg_mode == 2) bank = p;
                else if (prg_mode == 3) bank = c->prg_banks - 1;
                else                    bank = (p & ~1) + 1;
            }
            bank %= c->prg_banks;
            return c->prg[(bank * 16384) + (addr & 0x3FFF)];
        }
        case 2: { /* UNROM */
            if (addr < 0xC000) return c->prg[c->unrom_bank * 16384 + (addr & 0x3FFF)];
            return c->prg[(c->prg_banks - 1) * 16384 + (addr & 0x3FFF)];
        }
        case 3:
            bank = (addr < 0xC000) ? 0 : (c->prg_banks > 1 ? 1 : 0);
            return c->prg[(bank * 16384) + (addr & 0x3FFF)];
        default:
            return c->prg[(addr - 0x8000) % (c->prg_banks * 16384)];
    }
}

void cart_prg_write(Cart *c, u16 addr, u8 val) {
    switch(c->mapper) {
        case 1: { /* MMC1 */
            if (val & 0x80) {
                c->mmc1_shift = 0x10; c->mmc1_count = 0;
                c->mmc1_ctrl |= 0x0C; return;
            }
            c->mmc1_shift = ((val & 1) << 4) | (c->mmc1_shift >> 1);
            c->mmc1_count++;
            if (c->mmc1_count == 5) {
                u8 reg = (addr >> 13) & 3;
                switch(reg) {
                    case 0: c->mmc1_ctrl = c->mmc1_shift; break;
                    case 1: c->mmc1_chr0 = c->mmc1_shift; break;
                    case 2: c->mmc1_chr1 = c->mmc1_shift; break;
                    case 3: c->mmc1_prg  = c->mmc1_shift; break;
                }
                /* Update mirroring */
                switch(c->mmc1_ctrl & 3) {
                    case 0: c->mirror = 2; break;
                    case 1: c->mirror = 3; break;
                    case 2: c->mirror = 0; break;
                    case 3: c->mirror = 1; break;
                }
                c->mmc1_shift = 0x10; c->mmc1_count = 0;
            }
            break;
        }
        case 2: c->unrom_bank = val % c->prg_banks; break;
        case 3: c->cnrom_bank = val & 3; break;
        default: break;
    }
}

/* CHR read */
u8 cart_chr_read(Cart *c, u16 addr) {
    if (c->chr_is_ram) return c->chr_ram[addr & 0x1FFF];
    switch(c->mapper) {
        case 1: {
            int chr_mode = (c->mmc1_ctrl >> 4) & 1;
            int bank;
            if (chr_mode == 0) {
                bank = (c->mmc1_chr0 & ~1) % c->chr_banks;
                return c->chr[(bank * 8192) + (addr & 0x1FFF)];
            } else {
                if (addr < 0x1000) {
                    bank = c->mmc1_chr0 % (c->chr_banks * 2);
                    return c->chr[(bank * 4096) + (addr & 0x0FFF)];
                } else {
                    bank = c->mmc1_chr1 % (c->chr_banks * 2);
                    return c->chr[(bank * 4096) + (addr & 0x0FFF)];
                }
            }
        }
        case 3: {
            int bank = c->cnrom_bank % (c->chr_banks);
            return c->chr[(bank * 8192) + (addr & 0x1FFF)];
        }
        default:
            return c->chr[addr % (c->chr_banks * 8192)];
    }
}

void cart_chr_write(Cart *c, u16 addr, u8 val) {
    if (c->chr_is_ram) c->chr_ram[addr & 0x1FFF] = val;
}

/* ======================================================
   PPU
   ====================================================== */
typedef struct {
    Cart *cart;

    u8 vram[0x800];
    u8 oam[256];
    u8 palette[32];

    /* Registers */
    u8  ctrl, mask, status, oam_addr;
    /* Loopy scroll */
    u16 v, t;
    u8  x_fine, w;
    u8  read_buf;

    /* Rendering position */
    int scanline, dot;
    int odd_frame;
    int frame_ready;

    /* BG fetching latches */
    u8  nt_latch, at_latch, bg_lo_latch, bg_hi_latch;
    /* BG shift registers */
    u16 bg_sh_lo, bg_sh_hi;
    u16 at_sh_lo, at_sh_hi;

    /* Sprite data for current scanline */
    u8  soam[32];
    u8  sp_lo[8], sp_hi[8], sp_at[8], sp_x[8];
    int sp_cnt;
    int sp0_next, sp0_cur;

    int nmi_line;

    u32 pixels[256 * 240];
} PPU;

static int rendering_on(PPU *p) { return p->mask & 0x18; }

static u16 mirror_addr(PPU *p, u16 addr) {
    addr &= 0x0FFF;
    int nt = addr >> 10, off = addr & 0x3FF;
    switch(p->cart->mirror) {
        case 0: return ((nt & 2) >> 1) * 0x400 + off; /* horizontal */
        case 1: return (nt & 1) * 0x400 + off;         /* vertical   */
        case 2: return off;                              /* single 0   */
        case 3: return 0x400 + off;                     /* single 1   */
        default: return addr & 0x7FF;                   /* four-screen */
    }
}

static u8 ppu_mem_read(PPU *p, u16 addr) {
    addr &= 0x3FFF;
    if (addr < 0x2000) return cart_chr_read(p->cart, addr);
    if (addr < 0x3F00) return p->vram[mirror_addr(p, addr - 0x2000)];
    addr &= 0x1F;
    if (addr == 0x10) addr = 0x00;
    if (addr == 0x14) addr = 0x04;
    if (addr == 0x18) addr = 0x08;
    if (addr == 0x1C) addr = 0x0C;
    return p->palette[addr];
}

static void ppu_mem_write(PPU *p, u16 addr, u8 val) {
    addr &= 0x3FFF;
    if (addr < 0x2000) { cart_chr_write(p->cart, addr, val); return; }
    if (addr < 0x3F00) { p->vram[mirror_addr(p, addr - 0x2000)] = val; return; }
    addr &= 0x1F;
    if (addr == 0x10) addr = 0x00;
    if (addr == 0x14) addr = 0x04;
    if (addr == 0x18) addr = 0x08;
    if (addr == 0x1C) addr = 0x0C;
    p->palette[addr] = val;
}

u8 ppu_reg_read(PPU *p, u8 reg) {
    u8 val = 0;
    switch(reg & 7) {
        case 2:
            val = p->status;
            p->status &= ~0x80;
            p->w = 0;
            p->nmi_line = 0;
            break;
        case 4: val = p->oam[p->oam_addr]; break;
        case 7:
            if ((p->v & 0x3FFF) >= 0x3F00) {
                val = ppu_mem_read(p, p->v);
                p->read_buf = ppu_mem_read(p, 0x2000 | (p->v & 0x0FFF));
            } else {
                val = p->read_buf;
                p->read_buf = ppu_mem_read(p, p->v);
            }
            p->v += (p->ctrl & 0x04) ? 32 : 1;
            break;
    }
    return val;
}

int g_frame = 0; /* updated each frame for tracing */

void ppu_reg_write(PPU *p, u8 reg, u8 val) {
    switch(reg & 7) {
        case 0: {
            if (g_frame >= 31 && g_frame <= 36)
                fprintf(stderr, "  [F%d PPUCTRL] $%02X->$%02X SL=%d dot=%d\n",
                    g_frame, p->ctrl, val, p->scanline, p->dot);
            p->ctrl = val;
            p->t = (p->t & 0xF3FF) | ((u16)(val & 3) << 10);
            /* If NMI just enabled while we are in VBlank scanlines (241-260),
               fire NMI immediately. Use scanline position, NOT status flag,
               because the game may have already cleared the flag via $2002 read. */
            if ((val & 0x80) && (p->scanline >= 241 && p->scanline <= 260))
                p->nmi_line = 1;
            break;
        }
        case 1: p->mask = val; break;
        case 3: p->oam_addr = val; break;
        case 4: p->oam[p->oam_addr++] = val; break;
        case 5:
            if (!p->w) {
                p->t = (p->t & 0xFFE0) | (val >> 3);
                p->x_fine = val & 7;
            } else {
                p->t = (p->t & 0x8FFF) | ((u16)(val & 7) << 12);
                p->t = (p->t & 0xFC1F) | ((u16)(val >> 3) << 5);
            }
            p->w ^= 1;
            break;
        case 6:
            if (!p->w) {
                p->t = (p->t & 0x00FF) | ((u16)(val & 0x3F) << 8);
            } else {
                p->t = (p->t & 0xFF00) | val;
                p->v = p->t;
            }
            p->w ^= 1;
            break;
        case 7:
            ppu_mem_write(p, p->v, val);
            p->v += (p->ctrl & 0x04) ? 32 : 1;
            break;
    }
}

static void inc_x(PPU *p) {
    if ((p->v & 0x001F) == 31) { p->v &= ~0x001F; p->v ^= 0x0400; }
    else p->v++;
}

static void inc_y(PPU *p) {
    if ((p->v & 0x7000) != 0x7000) { p->v += 0x1000; return; }
    p->v &= ~0x7000;
    int y = (p->v >> 5) & 0x1F;
    if (y == 29) { y = 0; p->v ^= 0x0800; }
    else if (y == 31) y = 0;
    else y++;
    p->v = (p->v & ~0x03E0) | (y << 5);
}

static void copy_x(PPU *p) { p->v = (p->v & ~0x041F) | (p->t & 0x041F); }
static void copy_y(PPU *p) { p->v = (p->v & ~0x7BE0) | (p->t & 0x7BE0); }

static void reload_shifters(PPU *p) {
    p->bg_sh_lo = (p->bg_sh_lo & 0xFF00) | p->bg_lo_latch;
    p->bg_sh_hi = (p->bg_sh_hi & 0xFF00) | p->bg_hi_latch;
    p->at_sh_lo = (p->at_sh_lo & 0xFF00) | ((p->at_latch & 1) ? 0xFF : 0x00);
    p->at_sh_hi = (p->at_sh_hi & 0xFF00) | ((p->at_latch & 2) ? 0xFF : 0x00);
}

static void shift_bg(PPU *p) {
    p->bg_sh_lo <<= 1;
    p->bg_sh_hi <<= 1;
    p->at_sh_lo <<= 1;
    p->at_sh_hi <<= 1;
}

static void do_bg_fetch(PPU *p) {
    u16 pt_base = (p->ctrl & 0x10) ? 0x1000 : 0;
    u16 fine_y  = (p->v >> 12) & 7;
    switch(p->dot & 7) {
        case 1:
            reload_shifters(p);
            p->nt_latch = ppu_mem_read(p, 0x2000 | (p->v & 0x0FFF));
            break;
        case 3: {
            u16 at = ppu_mem_read(p, 0x23C0 | (p->v & 0x0C00)
                                          | ((p->v >> 4) & 0x38)
                                          | ((p->v >> 2) & 0x07));
            u8 shift = ((p->v >> 4) & 4) | (p->v & 2);
            p->at_latch = (at >> shift) & 3;
            break;
        }
        case 5:
            p->bg_lo_latch = ppu_mem_read(p, pt_base + (u16)p->nt_latch * 16 + fine_y);
            break;
        case 7:
            p->bg_hi_latch = ppu_mem_read(p, pt_base + (u16)p->nt_latch * 16 + fine_y + 8);
            break;
        case 0:
            if (p->dot == 256) inc_y(p);
            else               inc_x(p);
            break;
    }
}

/* Sprite evaluation for next scanline */
static void eval_sprites(PPU *p) {
    p->sp_cnt  = 0;
    p->sp0_next = 0;
    memset(p->soam, 0xFF, 32);

    int h = (p->ctrl & 0x20) ? 16 : 8;
    for (int i = 0; i < 64 && p->sp_cnt < 8; i++) {
        int sy = (int)p->oam[i * 4] + 1;
        if (p->scanline < sy || p->scanline >= sy + h) continue;
        p->soam[p->sp_cnt * 4 + 0] = p->oam[i * 4 + 0];
        p->soam[p->sp_cnt * 4 + 1] = p->oam[i * 4 + 1];
        p->soam[p->sp_cnt * 4 + 2] = p->oam[i * 4 + 2];
        p->soam[p->sp_cnt * 4 + 3] = p->oam[i * 4 + 3];
        if (i == 0) p->sp0_next = 1;
        p->sp_cnt++;
    }
    if (p->sp_cnt >= 8) p->status |= 0x20;
}

/* Load sprite tiles for the scanline just evaluated */
static void load_sprites(PPU *p) {
    int h = (p->ctrl & 0x20) ? 16 : 8;
    for (int i = 0; i < p->sp_cnt; i++) {
        u8 sy   = p->soam[i * 4 + 0];
        u8 tile = p->soam[i * 4 + 1];
        u8 attr = p->soam[i * 4 + 2];
        p->sp_at[i] = attr;
        p->sp_x[i]  = p->soam[i * 4 + 3];

        int row = p->scanline - (int)sy - 1;
        if (attr & 0x80) row = (h - 1) - row; /* vertical flip */

        u16 pt, t;
        if (h == 16) {
            pt = (tile & 1) ? 0x1000 : 0;
            t  = tile & 0xFE;
            if (row >= 8) { t++; row -= 8; }
        } else {
            pt = (p->ctrl & 0x08) ? 0x1000 : 0;
            t  = tile;
        }

        p->sp_lo[i] = ppu_mem_read(p, pt + t * 16 + row);
        p->sp_hi[i] = ppu_mem_read(p, pt + t * 16 + row + 8);
    }
}

/* One PPU clock */
int ppu_clock(PPU *p) {
    int nmi = 0;

    int visible   = (p->scanline >= 0  && p->scanline <= 239);
    int prerender = (p->scanline == 261);
    int render_line = (visible || prerender);
    int fetch_cycle = ((p->dot >= 1 && p->dot <= 256) || (p->dot >= 321 && p->dot <= 336));

    /* VBlank set */
    if (p->scanline == 241 && p->dot == 1) {
        p->status |= 0x80;
        if (p->ctrl & 0x80) { p->nmi_line = 1; }
    }

    /* VBlank clear on pre-render */
    if (prerender && p->dot == 1) {
        p->status &= ~0xE0;
        p->nmi_line = 0;
        p->sp0_cur = p->sp0_next;
    }

    /* NMI edge detection */
    if (p->nmi_line && (p->ctrl & 0x80)) {
        nmi = 1;
        p->nmi_line = 0;
    }

    if (rendering_on(p)) {
        /* Draw visible pixel */
        if (visible && p->dot >= 1 && p->dot <= 256) {
            int px = p->dot - 1, py = p->scanline;
            u16 bit = 0x8000 >> p->x_fine;

            /* BG */
            u8 bg_pix = 0, bg_pal = 0;
            if (p->mask & 0x08) {
                bg_pix = ((p->bg_sh_lo & bit) ? 1 : 0) | ((p->bg_sh_hi & bit) ? 2 : 0);
                bg_pal = ((p->at_sh_lo & bit) ? 1 : 0) | ((p->at_sh_hi & bit) ? 2 : 0);
            }

            /* Sprites */
            u8 sp_pix = 0, sp_pal = 0, sp_pri = 0, sp0 = 0;
            if (p->mask & 0x10) {
                for (int i = 0; i < p->sp_cnt; i++) {
                    int sx = px - (int)p->sp_x[i];
                    if (sx < 0 || sx > 7) continue;
                    int bit_pos = (p->sp_at[i] & 0x40) ? sx : (7 - sx);
                    u8 lo = (p->sp_lo[i] >> bit_pos) & 1;
                    u8 hi = (p->sp_hi[i] >> bit_pos) & 1;
                    u8 px2 = (hi << 1) | lo;
                    if (!px2) continue;
                    sp_pix = px2;
                    sp_pal = (p->sp_at[i] & 3) + 4;
                    sp_pri = (p->sp_at[i] >> 5) & 1;
                    sp0    = (i == 0 && p->sp0_cur);
                    break;
                }
            }

            /* Sprite 0 hit */
            if (sp0 && bg_pix && sp_pix && px < 255)
                p->status |= 0x40;

            /* Mux */
            u8 fin_pix, fin_pal;
            if (!bg_pix && !sp_pix) { fin_pix = 0; fin_pal = 0; }
            else if (!bg_pix)       { fin_pix = sp_pix; fin_pal = sp_pal; }
            else if (!sp_pix)       { fin_pix = bg_pix; fin_pal = bg_pal; }
            else {
                fin_pix = sp_pri ? bg_pix : sp_pix;
                fin_pal = sp_pri ? bg_pal : sp_pal;
            }

            u8 color = ppu_mem_read(p, 0x3F00 + (fin_pal << 2) + fin_pix) & 0x3F;
            p->pixels[py * 256 + px] = NES_PALETTE[color];
        }

        /* BG fetches */
        if (render_line && fetch_cycle)
            do_bg_fetch(p);

        /* Shift BG */
        if (render_line && ((p->dot >= 1 && p->dot <= 256) || (p->dot >= 321 && p->dot <= 336)))
            shift_bg(p);

        /* End of visible line: sprite eval + copy_x */
        if (render_line && p->dot == 257) {
            reload_shifters(p);
            copy_x(p);
            if (visible) eval_sprites(p);
        }

        /* Dummy NT fetches 337-340 */
        if (render_line && (p->dot == 337 || p->dot == 339))
            reload_shifters(p);

        /* Start of line: load sprites */
        if (p->dot == 320 && render_line)
            load_sprites(p);

        /* Pre-render copy Y */
        if (prerender && p->dot >= 280 && p->dot <= 304)
            copy_y(p);
    }

    /* Advance dot/scanline */
    p->dot++;
    if (p->dot > 340) {
        p->dot = 0;
        p->scanline++;
        if (p->scanline > 261) {
            p->scanline = 0;
            p->odd_frame ^= 1;
            p->frame_ready = 1;
        }
    }
    /* Skip cycle on odd frames */
    if (prerender && p->odd_frame && p->dot == 0 && rendering_on(p))
        p->dot = 1;

    return nmi;
}

/* ======================================================
   CPU  (MOS 6502)
   ====================================================== */
typedef struct {
    u16 PC;
    u8  A, X, Y, S, P;
    u64 cycles;
    int halt;

    PPU  *ppu;
    Cart *cart;
    u8    ram[0x800];

    /* Controller */
    u8 joy[2], joy_shift[2], joy_strobe;

    /* OAM DMA */
    int dma_active;
    u8  dma_page;
    int dma_cycle;
} CPU;

#define FL_C 0x01
#define FL_Z 0x02
#define FL_I 0x04
#define FL_D 0x08
#define FL_B 0x10
#define FL_U 0x20
#define FL_V 0x40
#define FL_N 0x80

static inline void set_nz(CPU *c, u8 v) {
    c->P = (c->P & ~(FL_N|FL_Z)) | (v ? 0 : FL_Z) | (v & FL_N);
}

u8   cpu_read(CPU *c, u16 addr);
extern int g_frame;
void cpu_write(CPU *c, u16 addr, u8 val);

static inline u8  rd8(CPU *c)  { return cpu_read(c, c->PC++); }
static inline u16 rd16(CPU *c) { u16 lo = rd8(c); return lo | ((u16)rd8(c) << 8); }
static inline void push8(CPU *c, u8 v)  { cpu_write(c, 0x100 | c->S--, v); }
static inline void push16(CPU *c, u16 v){ push8(c, v >> 8); push8(c, v & 0xFF); }
static inline u8  pop8(CPU *c)          { return cpu_read(c, 0x100 | ++c->S); }
static inline u16 pop16(CPU *c)         { u16 l = pop8(c); return l | ((u16)pop8(c) << 8); }

static inline u16 rw_bug(CPU *c, u16 a) {
    u8 lo = cpu_read(c, a);
    u8 hi = cpu_read(c, (a & 0xFF00) | ((a + 1) & 0x00FF));
    return lo | ((u16)hi << 8);
}

u8 cpu_read(CPU *c, u16 addr) {
    if (addr < 0x2000) {
        u8 r = c->ram[addr & 0x7FF];
        if (g_frame >= 31 && g_frame <= 36 && c->PC >= 0x814E && c->PC <= 0x8158)
            fprintf(stderr, "  [F%d RAM] PC=$%04X read [$%04X]=$%02X\n", g_frame, c->PC-1, addr, r);
        return r;
    }
    if (addr < 0x4000) return ppu_reg_read(c->ppu, addr & 7);
    if (addr == 0x4016) {
        u8 v = (c->joy_shift[0] >> 7) & 1;
        if (!c->joy_strobe) c->joy_shift[0] <<= 1;
        else c->joy_shift[0] = c->joy[0];
        return v;
    }
    if (addr == 0x4017) {
        u8 v = (c->joy_shift[1] >> 7) & 1;
        if (!c->joy_strobe) c->joy_shift[1] <<= 1;
        else c->joy_shift[1] = c->joy[1];
        return v;
    }
    if (addr >= 0x8000) return cart_prg_read(c->cart, addr);
    return 0;
}

void cpu_write(CPU *c, u16 addr, u8 val) {
    if (addr < 0x2000) { c->ram[addr & 0x7FF] = val; return; }
    if (addr < 0x4000) { ppu_reg_write(c->ppu, addr & 7, val); return; }
    if (addr == 0x4014) {
        c->dma_page   = val;
        c->dma_active = 1;
        c->dma_cycle  = 0;
        return;
    }
    if (addr == 0x4016) {
        u8 old = c->joy_strobe;
        c->joy_strobe = val & 1;
        if (old && !c->joy_strobe) {
            c->joy_shift[0] = c->joy[0];
            c->joy_shift[1] = c->joy[1];
        }
        return;
    }
    if (addr >= 0x8000) { cart_prg_write(c->cart, addr, val); return; }
}

static void cpu_nmi(CPU *c) {
    push16(c, c->PC);
    push8(c, (c->P | FL_U) & ~FL_B);
    c->P   |= FL_I;
    c->PC   = cpu_read(c, 0xFFFA) | ((u16)cpu_read(c, 0xFFFB) << 8);
    c->cycles += 7;
}

/* Branch helper: 2 + 1 if taken + 1 if page cross */
static inline void branch(CPU *c, int cond, s8 off) {
    c->cycles += 2;
    if (!cond) return;
    c->cycles++;
    u16 old = c->PC;
    c->PC += (s16)off;
    if ((old & 0xFF00) != (c->PC & 0xFF00)) c->cycles++;
}

/* ADC core */
static inline void do_adc(CPU *c, u8 v) {
    u16 r = (u16)c->A + v + (c->P & FL_C);
    u8  overflow = (~(c->A ^ v) & (c->A ^ (u8)r) & 0x80) ? FL_V : 0;
    c->P = (c->P & ~(FL_C|FL_Z|FL_N|FL_V))
         | (r > 0xFF ? FL_C : 0)
         | overflow;
    c->A = (u8)r;
    set_nz(c, c->A);
}

static inline void do_sbc(CPU *c, u8 v) { do_adc(c, ~v); }

/* CMP core */
static inline void do_cmp(CPU *c, u8 a, u8 b) {
    u16 r = (u16)a - b;
    c->P = (c->P & ~(FL_C|FL_Z|FL_N))
         | (a >= b ? FL_C : 0)
         | (!(r & 0xFF) ? FL_Z : 0)
         | (r & FL_N);
}

/* Execute one instruction, return cycles used (not counting DMA) */
int cpu_step(CPU *c) {
    if (c->halt) return 1;

    u8 op = rd8(c);
    int cy = 0;
    u8  tmp8;
    u16 tmp16;
    s8  rel;

    switch(op) {
        /* ---- LDA ---- */
        case 0xA9: c->A = rd8(c); set_nz(c,c->A); cy=2; break;
        case 0xA5: c->A = cpu_read(c, rd8(c)); set_nz(c,c->A); cy=3; break;
        case 0xB5: c->A = cpu_read(c,(rd8(c)+c->X)&0xFF); set_nz(c,c->A); cy=4; break;
        case 0xAD: c->A = cpu_read(c, rd16(c)); set_nz(c,c->A); cy=4; break;
        case 0xBD: tmp16=rd16(c); c->A=cpu_read(c,tmp16+c->X); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0xB9: tmp16=rd16(c); c->A=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0xA1: tmp8=(rd8(c)+c->X)&0xFF; c->A=cpu_read(c,rw_bug(c,tmp8)); set_nz(c,c->A); cy=6; break;
        case 0xB1: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); c->A=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=5+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- LDX ---- */
        case 0xA2: c->X=rd8(c); set_nz(c,c->X); cy=2; break;
        case 0xA6: c->X=cpu_read(c,rd8(c)); set_nz(c,c->X); cy=3; break;
        case 0xB6: c->X=cpu_read(c,(rd8(c)+c->Y)&0xFF); set_nz(c,c->X); cy=4; break;
        case 0xAE: c->X=cpu_read(c,rd16(c)); set_nz(c,c->X); cy=4; break;
        case 0xBE: tmp16=rd16(c); c->X=cpu_read(c,tmp16+c->Y); set_nz(c,c->X); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- LDY ---- */
        case 0xA0: c->Y=rd8(c); set_nz(c,c->Y); cy=2; break;
        case 0xA4: c->Y=cpu_read(c,rd8(c)); set_nz(c,c->Y); cy=3; break;
        case 0xB4: c->Y=cpu_read(c,(rd8(c)+c->X)&0xFF); set_nz(c,c->Y); cy=4; break;
        case 0xAC: c->Y=cpu_read(c,rd16(c)); set_nz(c,c->Y); cy=4; break;
        case 0xBC: tmp16=rd16(c); c->Y=cpu_read(c,tmp16+c->X); set_nz(c,c->Y); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        /* ---- STA ---- */
        case 0x85: cpu_write(c,rd8(c),c->A); cy=3; break;
        case 0x95: cpu_write(c,(rd8(c)+c->X)&0xFF,c->A); cy=4; break;
        case 0x8D: cpu_write(c,rd16(c),c->A); cy=4; break;
        case 0x9D: tmp16=rd16(c); cpu_write(c,tmp16+c->X,c->A); cy=5; break;
        case 0x99: tmp16=rd16(c); cpu_write(c,tmp16+c->Y,c->A); cy=5; break;
        case 0x81: tmp8=(rd8(c)+c->X)&0xFF; cpu_write(c,rw_bug(c,tmp8),c->A); cy=6; break;
        case 0x91: tmp8=rd8(c); cpu_write(c,rw_bug(c,tmp8)+c->Y,c->A); cy=6; break;
        /* ---- STX ---- */
        case 0x86: cpu_write(c,rd8(c),c->X); cy=3; break;
        case 0x96: cpu_write(c,(rd8(c)+c->Y)&0xFF,c->X); cy=4; break;
        case 0x8E: cpu_write(c,rd16(c),c->X); cy=4; break;
        /* ---- STY ---- */
        case 0x84: cpu_write(c,rd8(c),c->Y); cy=3; break;
        case 0x94: cpu_write(c,(rd8(c)+c->X)&0xFF,c->Y); cy=4; break;
        case 0x8C: cpu_write(c,rd16(c),c->Y); cy=4; break;
        /* ---- Transfers ---- */
        case 0xAA: c->X=c->A; set_nz(c,c->X); cy=2; break;
        case 0xA8: c->Y=c->A; set_nz(c,c->Y); cy=2; break;
        case 0x8A: c->A=c->X; set_nz(c,c->A); cy=2; break;
        case 0x98: c->A=c->Y; set_nz(c,c->A); cy=2; break;
        case 0xBA: c->X=c->S; set_nz(c,c->X); cy=2; break;
        case 0x9A: c->S=c->X; cy=2; break;
        /* ---- Stack ---- */
        case 0x48: push8(c,c->A); cy=3; break;
        case 0x08: push8(c,c->P|FL_B|FL_U); cy=3; break;
        case 0x68: c->A=pop8(c); set_nz(c,c->A); cy=4; break;
        case 0x28: c->P=pop8(c)|FL_U; cy=4; break;
        /* ---- ADC ---- */
        case 0x69: do_adc(c,rd8(c)); cy=2; break;
        case 0x65: do_adc(c,cpu_read(c,rd8(c))); cy=3; break;
        case 0x75: do_adc(c,cpu_read(c,(rd8(c)+c->X)&0xFF)); cy=4; break;
        case 0x6D: do_adc(c,cpu_read(c,rd16(c))); cy=4; break;
        case 0x7D: tmp16=rd16(c); do_adc(c,cpu_read(c,tmp16+c->X)); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0x79: tmp16=rd16(c); do_adc(c,cpu_read(c,tmp16+c->Y)); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0x61: tmp8=(rd8(c)+c->X)&0xFF; do_adc(c,cpu_read(c,rw_bug(c,tmp8))); cy=6; break;
        case 0x71: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); do_adc(c,cpu_read(c,tmp16+c->Y)); cy=5+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- SBC ---- */
        case 0xE9: case 0xEB: do_sbc(c,rd8(c)); cy=2; break;
        case 0xE5: do_sbc(c,cpu_read(c,rd8(c))); cy=3; break;
        case 0xF5: do_sbc(c,cpu_read(c,(rd8(c)+c->X)&0xFF)); cy=4; break;
        case 0xED: do_sbc(c,cpu_read(c,rd16(c))); cy=4; break;
        case 0xFD: tmp16=rd16(c); do_sbc(c,cpu_read(c,tmp16+c->X)); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0xF9: tmp16=rd16(c); do_sbc(c,cpu_read(c,tmp16+c->Y)); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0xE1: tmp8=(rd8(c)+c->X)&0xFF; do_sbc(c,cpu_read(c,rw_bug(c,tmp8))); cy=6; break;
        case 0xF1: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); do_sbc(c,cpu_read(c,tmp16+c->Y)); cy=5+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- AND ---- */
        case 0x29: c->A&=rd8(c); set_nz(c,c->A); cy=2; break;
        case 0x25: c->A&=cpu_read(c,rd8(c)); set_nz(c,c->A); cy=3; break;
        case 0x35: c->A&=cpu_read(c,(rd8(c)+c->X)&0xFF); set_nz(c,c->A); cy=4; break;
        case 0x2D: c->A&=cpu_read(c,rd16(c)); set_nz(c,c->A); cy=4; break;
        case 0x3D: tmp16=rd16(c); c->A&=cpu_read(c,tmp16+c->X); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0x39: tmp16=rd16(c); c->A&=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0x21: tmp8=(rd8(c)+c->X)&0xFF; c->A&=cpu_read(c,rw_bug(c,tmp8)); set_nz(c,c->A); cy=6; break;
        case 0x31: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); c->A&=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=5+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- ORA ---- */
        case 0x09: c->A|=rd8(c); set_nz(c,c->A); cy=2; break;
        case 0x05: c->A|=cpu_read(c,rd8(c)); set_nz(c,c->A); cy=3; break;
        case 0x15: c->A|=cpu_read(c,(rd8(c)+c->X)&0xFF); set_nz(c,c->A); cy=4; break;
        case 0x0D: c->A|=cpu_read(c,rd16(c)); set_nz(c,c->A); cy=4; break;
        case 0x1D: tmp16=rd16(c); c->A|=cpu_read(c,tmp16+c->X); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0x19: tmp16=rd16(c); c->A|=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0x01: tmp8=(rd8(c)+c->X)&0xFF; c->A|=cpu_read(c,rw_bug(c,tmp8)); set_nz(c,c->A); cy=6; break;
        case 0x11: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); c->A|=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=5+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- EOR ---- */
        case 0x49: c->A^=rd8(c); set_nz(c,c->A); cy=2; break;
        case 0x45: c->A^=cpu_read(c,rd8(c)); set_nz(c,c->A); cy=3; break;
        case 0x55: c->A^=cpu_read(c,(rd8(c)+c->X)&0xFF); set_nz(c,c->A); cy=4; break;
        case 0x4D: c->A^=cpu_read(c,rd16(c)); set_nz(c,c->A); cy=4; break;
        case 0x5D: tmp16=rd16(c); c->A^=cpu_read(c,tmp16+c->X); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0x59: tmp16=rd16(c); c->A^=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0x41: tmp8=(rd8(c)+c->X)&0xFF; c->A^=cpu_read(c,rw_bug(c,tmp8)); set_nz(c,c->A); cy=6; break;
        case 0x51: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); c->A^=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=5+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- CMP ---- */
        case 0xC9: do_cmp(c,c->A,rd8(c)); cy=2; break;
        case 0xC5: do_cmp(c,c->A,cpu_read(c,rd8(c))); cy=3; break;
        case 0xD5: do_cmp(c,c->A,cpu_read(c,(rd8(c)+c->X)&0xFF)); cy=4; break;
        case 0xCD: do_cmp(c,c->A,cpu_read(c,rd16(c))); cy=4; break;
        case 0xDD: tmp16=rd16(c); do_cmp(c,c->A,cpu_read(c,tmp16+c->X)); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0xD9: tmp16=rd16(c); do_cmp(c,c->A,cpu_read(c,tmp16+c->Y)); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0xC1: tmp8=(rd8(c)+c->X)&0xFF; do_cmp(c,c->A,cpu_read(c,rw_bug(c,tmp8))); cy=6; break;
        case 0xD1: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); do_cmp(c,c->A,cpu_read(c,tmp16+c->Y)); cy=5+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        /* ---- CPX ---- */
        case 0xE0: do_cmp(c,c->X,rd8(c)); cy=2; break;
        case 0xE4: do_cmp(c,c->X,cpu_read(c,rd8(c))); cy=3; break;
        case 0xEC: do_cmp(c,c->X,cpu_read(c,rd16(c))); cy=4; break;
        /* ---- CPY ---- */
        case 0xC0: do_cmp(c,c->Y,rd8(c)); cy=2; break;
        case 0xC4: do_cmp(c,c->Y,cpu_read(c,rd8(c))); cy=3; break;
        case 0xCC: do_cmp(c,c->Y,cpu_read(c,rd16(c))); cy=4; break;
        /* ---- INC ---- */
        case 0xE6: tmp8=rd8(c); tmp16=cpu_read(c,tmp8)+1; cpu_write(c,tmp8,tmp16); set_nz(c,tmp16); cy=5; break;
        case 0xF6: tmp8=(rd8(c)+c->X)&0xFF; tmp16=cpu_read(c,tmp8)+1; cpu_write(c,tmp8,tmp16); set_nz(c,tmp16); cy=6; break;
        case 0xEE: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16)+1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=6; break;
        case 0xFE: tmp16=rd16(c)+c->X; { u8 v=cpu_read(c,tmp16)+1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=7; break;
        /* ---- DEC ---- */
        case 0xC6: tmp8=rd8(c); tmp16=cpu_read(c,tmp8)-1; cpu_write(c,tmp8,tmp16); set_nz(c,tmp16); cy=5; break;
        case 0xD6: tmp8=(rd8(c)+c->X)&0xFF; tmp16=cpu_read(c,tmp8)-1; cpu_write(c,tmp8,tmp16); set_nz(c,tmp16); cy=6; break;
        case 0xCE: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16)-1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=6; break;
        case 0xDE: tmp16=rd16(c)+c->X; { u8 v=cpu_read(c,tmp16)-1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=7; break;
        /* ---- INX/INY/DEX/DEY ---- */
        case 0xE8: c->X++; set_nz(c,c->X); cy=2; break;
        case 0xC8: c->Y++; set_nz(c,c->Y); cy=2; break;
        case 0xCA: c->X--; set_nz(c,c->X); cy=2; break;
        case 0x88: c->Y--; set_nz(c,c->Y); cy=2; break;
        /* ---- ASL ---- */
        case 0x0A: c->P=(c->P&~FL_C)|(c->A>>7); c->A<<=1; set_nz(c,c->A); cy=2; break;
        case 0x06: tmp8=rd8(c); { u8 v=cpu_read(c,tmp8); c->P=(c->P&~FL_C)|(v>>7); v<<=1; cpu_write(c,tmp8,v); set_nz(c,v); } cy=5; break;
        case 0x16: tmp8=(rd8(c)+c->X)&0xFF; { u8 v=cpu_read(c,tmp8); c->P=(c->P&~FL_C)|(v>>7); v<<=1; cpu_write(c,tmp8,v); set_nz(c,v); } cy=6; break;
        case 0x0E: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16); c->P=(c->P&~FL_C)|(v>>7); v<<=1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=6; break;
        case 0x1E: tmp16=rd16(c)+c->X; { u8 v=cpu_read(c,tmp16); c->P=(c->P&~FL_C)|(v>>7); v<<=1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=7; break;
        /* ---- LSR ---- */
        case 0x4A: c->P=(c->P&~FL_C)|(c->A&1); c->A>>=1; set_nz(c,c->A); cy=2; break;
        case 0x46: tmp8=rd8(c); { u8 v=cpu_read(c,tmp8); c->P=(c->P&~FL_C)|(v&1); v>>=1; cpu_write(c,tmp8,v); set_nz(c,v); } cy=5; break;
        case 0x56: tmp8=(rd8(c)+c->X)&0xFF; { u8 v=cpu_read(c,tmp8); c->P=(c->P&~FL_C)|(v&1); v>>=1; cpu_write(c,tmp8,v); set_nz(c,v); } cy=6; break;
        case 0x4E: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16); c->P=(c->P&~FL_C)|(v&1); v>>=1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=6; break;
        case 0x5E: tmp16=rd16(c)+c->X; { u8 v=cpu_read(c,tmp16); c->P=(c->P&~FL_C)|(v&1); v>>=1; cpu_write(c,tmp16,v); set_nz(c,v); } cy=7; break;
        /* ---- ROL ---- */
        case 0x2A: { u8 oc=c->P&FL_C; c->P=(c->P&~FL_C)|(c->A>>7); c->A=(c->A<<1)|oc; set_nz(c,c->A); cy=2; break; }
        case 0x26: tmp8=rd8(c); { u8 v=cpu_read(c,tmp8),oc=c->P&FL_C; c->P=(c->P&~FL_C)|(v>>7); v=(v<<1)|oc; cpu_write(c,tmp8,v); set_nz(c,v); } cy=5; break;
        case 0x36: tmp8=(rd8(c)+c->X)&0xFF; { u8 v=cpu_read(c,tmp8),oc=c->P&FL_C; c->P=(c->P&~FL_C)|(v>>7); v=(v<<1)|oc; cpu_write(c,tmp8,v); set_nz(c,v); } cy=6; break;
        case 0x2E: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16),oc=c->P&FL_C; c->P=(c->P&~FL_C)|(v>>7); v=(v<<1)|oc; cpu_write(c,tmp16,v); set_nz(c,v); } cy=6; break;
        case 0x3E: tmp16=rd16(c)+c->X; { u8 v=cpu_read(c,tmp16),oc=c->P&FL_C; c->P=(c->P&~FL_C)|(v>>7); v=(v<<1)|oc; cpu_write(c,tmp16,v); set_nz(c,v); } cy=7; break;
        /* ---- ROR ---- */
        case 0x6A: { u8 oc=(c->P&FL_C)<<7; c->P=(c->P&~FL_C)|(c->A&1); c->A=(c->A>>1)|oc; set_nz(c,c->A); cy=2; break; }
        case 0x66: tmp8=rd8(c); { u8 v=cpu_read(c,tmp8),oc=(c->P&FL_C)<<7; c->P=(c->P&~FL_C)|(v&1); v=(v>>1)|oc; cpu_write(c,tmp8,v); set_nz(c,v); } cy=5; break;
        case 0x76: tmp8=(rd8(c)+c->X)&0xFF; { u8 v=cpu_read(c,tmp8),oc=(c->P&FL_C)<<7; c->P=(c->P&~FL_C)|(v&1); v=(v>>1)|oc; cpu_write(c,tmp8,v); set_nz(c,v); } cy=6; break;
        case 0x6E: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16),oc=(c->P&FL_C)<<7; c->P=(c->P&~FL_C)|(v&1); v=(v>>1)|oc; cpu_write(c,tmp16,v); set_nz(c,v); } cy=6; break;
        case 0x7E: tmp16=rd16(c)+c->X; { u8 v=cpu_read(c,tmp16),oc=(c->P&FL_C)<<7; c->P=(c->P&~FL_C)|(v&1); v=(v>>1)|oc; cpu_write(c,tmp16,v); set_nz(c,v); } cy=7; break;
        /* ---- BIT ---- */
        case 0x24: tmp8=cpu_read(c,rd8(c)); c->P=(c->P&~(FL_V|FL_N|FL_Z))|(tmp8&0xC0)|(c->A&tmp8?0:FL_Z); cy=3; break;
        case 0x2C: tmp8=cpu_read(c,rd16(c)); c->P=(c->P&~(FL_V|FL_N|FL_Z))|(tmp8&0xC0)|(c->A&tmp8?0:FL_Z); cy=4; break;
        /* ---- Branches ---- */
        case 0x90: rel=(s8)rd8(c); branch(c,!(c->P&FL_C),rel); break; /* BCC */
        case 0xB0: rel=(s8)rd8(c); branch(c, (c->P&FL_C),rel); break; /* BCS */
        case 0xF0: rel=(s8)rd8(c); branch(c, (c->P&FL_Z),rel); break; /* BEQ */
        case 0xD0: rel=(s8)rd8(c); branch(c,!(c->P&FL_Z),rel); break; /* BNE */
        case 0x30: rel=(s8)rd8(c); branch(c, (c->P&FL_N),rel); break; /* BMI */
        case 0x10: rel=(s8)rd8(c); branch(c,!(c->P&FL_N),rel); break; /* BPL */
        case 0x50: rel=(s8)rd8(c); branch(c,!(c->P&FL_V),rel); break; /* BVC */
        case 0x70: rel=(s8)rd8(c); branch(c, (c->P&FL_V),rel); break; /* BVS */
        /* ---- JMP ---- */
        case 0x4C: c->PC=rd16(c); cy=3; break;
        case 0x6C: tmp16=rd16(c); c->PC=rw_bug(c,tmp16); cy=5; break;
        /* ---- JSR/RTS/RTI/BRK ---- */
        case 0x20: tmp16=rd16(c); push16(c,c->PC-1); c->PC=tmp16; cy=6; break;
        case 0x60: c->PC=pop16(c)+1; cy=6; break;
        case 0x40: c->P=pop8(c)|FL_U; c->PC=pop16(c); cy=6; break;
        case 0x00: rd8(c); push16(c,c->PC); push8(c,c->P|FL_B|FL_U); c->P|=FL_I;
                   c->PC=cpu_read(c,0xFFFE)|((u16)cpu_read(c,0xFFFF)<<8); cy=7; break;
        /* ---- Flag ops ---- */
        case 0x18: c->P&=~FL_C; cy=2; break;
        case 0x38: c->P|= FL_C; cy=2; break;
        case 0x58: c->P&=~FL_I; cy=2; break;
        case 0x78: c->P|= FL_I; cy=2; break;
        case 0xB8: c->P&=~FL_V; cy=2; break;
        case 0xD8: c->P&=~FL_D; cy=2; break;
        case 0xF8: c->P|= FL_D; cy=2; break;
        /* ---- NOP ---- */
        case 0xEA:
        case 0x1A: case 0x3A: case 0x5A: case 0x7A: case 0xDA: case 0xFA: cy=2; break;
        case 0x04: case 0x44: case 0x64: rd8(c); cy=3; break;
        case 0x14: case 0x34: case 0x54: case 0x74: case 0xD4: case 0xF4: rd8(c); cy=4; break;
        case 0x0C: rd16(c); cy=4; break;
        case 0x1C: case 0x3C: case 0x5C: case 0x7C: case 0xDC: case 0xFC:
            tmp16=rd16(c); cpu_read(c,tmp16+c->X); cy=4+((tmp16>>8)!=((tmp16+c->X)>>8)); break;
        case 0x80: case 0x82: case 0x89: case 0xC2: case 0xE2: rd8(c); cy=2; break;
        /* ---- Unofficial: LAX ---- */
        case 0xA7: c->A=c->X=cpu_read(c,rd8(c)); set_nz(c,c->A); cy=3; break;
        case 0xB7: c->A=c->X=cpu_read(c,(rd8(c)+c->Y)&0xFF); set_nz(c,c->A); cy=4; break;
        case 0xAF: c->A=c->X=cpu_read(c,rd16(c)); set_nz(c,c->A); cy=4; break;
        case 0xBF: tmp16=rd16(c); c->A=c->X=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=4+((tmp16>>8)!=((tmp16+c->Y)>>8)); break;
        case 0xA3: tmp8=(rd8(c)+c->X)&0xFF; c->A=c->X=cpu_read(c,rw_bug(c,tmp8)); set_nz(c,c->A); cy=6; break;
        case 0xB3: tmp8=rd8(c); tmp16=rw_bug(c,tmp8); c->A=c->X=cpu_read(c,tmp16+c->Y); set_nz(c,c->A); cy=5; break;
        /* ---- Unofficial: SAX ---- */
        case 0x87: cpu_write(c,rd8(c),c->A&c->X); cy=3; break;
        case 0x97: cpu_write(c,(rd8(c)+c->Y)&0xFF,c->A&c->X); cy=4; break;
        case 0x8F: cpu_write(c,rd16(c),c->A&c->X); cy=4; break;
        /* ---- Unofficial: DCP ---- */
        case 0xC7: tmp8=rd8(c); { u8 v=cpu_read(c,tmp8)-1; cpu_write(c,tmp8,v); do_cmp(c,c->A,v); } cy=5; break;
        case 0xD7: tmp8=(rd8(c)+c->X)&0xFF; { u8 v=cpu_read(c,tmp8)-1; cpu_write(c,tmp8,v); do_cmp(c,c->A,v); } cy=6; break;
        case 0xCF: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16)-1; cpu_write(c,tmp16,v); do_cmp(c,c->A,v); } cy=6; break;
        /* ---- Unofficial: ISC ---- */
        case 0xE7: tmp8=rd8(c); { u8 v=cpu_read(c,tmp8)+1; cpu_write(c,tmp8,v); do_sbc(c,v); } cy=5; break;
        case 0xF7: tmp8=(rd8(c)+c->X)&0xFF; { u8 v=cpu_read(c,tmp8)+1; cpu_write(c,tmp8,v); do_sbc(c,v); } cy=6; break;
        case 0xEF: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16)+1; cpu_write(c,tmp16,v); do_sbc(c,v); } cy=6; break;
        /* ---- Unofficial: SLO ---- */
        case 0x07: tmp8=rd8(c); { u8 v=cpu_read(c,tmp8); c->P=(c->P&~FL_C)|(v>>7); v<<=1; cpu_write(c,tmp8,v); c->A|=v; set_nz(c,c->A); } cy=5; break;
        case 0x17: tmp8=(rd8(c)+c->X)&0xFF; { u8 v=cpu_read(c,tmp8); c->P=(c->P&~FL_C)|(v>>7); v<<=1; cpu_write(c,tmp8,v); c->A|=v; set_nz(c,c->A); } cy=6; break;
        case 0x0F: tmp16=rd16(c); { u8 v=cpu_read(c,tmp16); c->P=(c->P&~FL_C)|(v>>7); v<<=1; cpu_write(c,tmp16,v); c->A|=v; set_nz(c,c->A); } cy=6; break;
        /* Catch-all for unknown opcodes */
        default: cy=2; break;
    }

    if (cy == 0) cy = 2;
    c->cycles += cy;
    return cy;
}

/* ======================================================
   RESET
   ====================================================== */
static void nes_reset(CPU *cpu) {
    cpu->A = cpu->X = cpu->Y = 0;
    cpu->S  = 0xFD;
    cpu->P  = FL_U | FL_I;
    cpu->PC = cpu_read(cpu, 0xFFFC) | ((u16)cpu_read(cpu, 0xFFFD) << 8);
    cpu->cycles = 0;
    cpu->dma_active = 0;
    cpu->halt = 0;
    /* PPU reset */
    PPU *p = cpu->ppu;
    memset(p->vram, 0, sizeof(p->vram));
    memset(p->oam,  0, sizeof(p->oam));
    memset(p->palette, 0, sizeof(p->palette));
    p->ctrl=p->mask=p->status=p->oam_addr=0;
    p->v=p->t=p->x_fine=p->w=0;
    p->read_buf=0;
    p->scanline=0; p->dot=0; p->odd_frame=0; p->frame_ready=0;
    p->nmi_line=0;
}

/* ======================================================
   MAIN
   ====================================================== */
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s game.nes\n", argv[0]);
        return 1;
    }

    Cart *cart = cart_load(argv[1]);
    if (!cart) return 1;

    PPU ppu;
    memset(&ppu, 0, sizeof(ppu));
    ppu.cart = cart;

    CPU cpu;
    memset(&cpu, 0, sizeof(cpu));
    cpu.ppu  = &ppu;
    cpu.cart = cart;

    nes_reset(&cpu);

    /* SDL Setup */
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) < 0) {
        fprintf(stderr, "SDL init failed: %s\n", SDL_GetError());
        return 1;
    }

    SDL_Window   *win = SDL_CreateWindow("NES Emulator",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        512, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE);
    SDL_Renderer *ren = SDL_CreateRenderer(win, -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    SDL_Texture  *tex = SDL_CreateTexture(ren,
        SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, 256, 240);

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_RenderSetLogicalSize(ren, 256, 240);

    int running = 1;
    while (running) {

        /* --- Poll events --- */
        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            if (ev.type == SDL_QUIT) running = 0;
            if (ev.type == SDL_KEYDOWN) {
                switch(ev.key.keysym.sym) {
                    case SDLK_ESCAPE: running = 0; break;
                    case SDLK_r: nes_reset(&cpu); break;
                    default: break;
                }
            }
        }

        /* --- Read controller --- */
        const u8 *ks = SDL_GetKeyboardState(NULL);
        cpu.joy[0] =
            ((ks[SDL_SCANCODE_Z]      ? 1 : 0) << 7) |
            ((ks[SDL_SCANCODE_X]      ? 1 : 0) << 6) |
            ((ks[SDL_SCANCODE_RSHIFT] ? 1 : 0) << 5) |
            ((ks[SDL_SCANCODE_RETURN] ? 1 : 0) << 4) |
            ((ks[SDL_SCANCODE_UP]     ? 1 : 0) << 3) |
            ((ks[SDL_SCANCODE_DOWN]   ? 1 : 0) << 2) |
            ((ks[SDL_SCANCODE_LEFT]   ? 1 : 0) << 1) |
            ((ks[SDL_SCANCODE_RIGHT]  ? 1 : 0) << 0);

        /*
         * Run CPU+PPU until the PPU signals a completed frame.
         * frame_ready is set when PPU scanline wraps 261->0.
         * Safety cap of 200000 CPU cycles guards against infinite loops.
         */
        ppu.frame_ready = 0;
        int safety = 0;
        int nmi_count = 0;
        while (!ppu.frame_ready && safety < 200000) {
            int cyc;

            if (cpu.dma_active) {
                u16 base = (u16)cpu.dma_page << 8;
                for (int i = 0; i < 256; i++)
                    cpu.ppu->oam[i] = cpu_read(&cpu, base + i);
                cpu.dma_active = 0;
                cyc = 513;
            } else {
                cyc = cpu_step(&cpu);
            }
            safety += cyc;

            for (int i = 0; i < cyc * 3; i++) {
                if (ppu_clock(&ppu)) {
                    nmi_count++;
                    cpu_nmi(&cpu);
                }
            }
        }

        static int frame_num = 0;
        frame_num++;
        g_frame = frame_num;

        if (frame_num <= 35)
            fprintf(stderr, "Frame %3d: safety=%6d frame_ready=%d nmis=%d PC=$%04X SL=%3d dot=%3d CTRL=$%02X MASK=$%02X STAT=$%02X\n",
                frame_num, safety, ppu.frame_ready, nmi_count,
                cpu.PC, ppu.scanline, ppu.dot,
                ppu.ctrl, ppu.mask, ppu.status);
        fflush(stderr);

        /* --- Blit PPU framebuffer to screen --- */
        void *pixels_sdl; int pitch;
        SDL_LockTexture(tex, NULL, &pixels_sdl, &pitch);
        memcpy(pixels_sdl, ppu.pixels, 256 * 240 * 4);
        SDL_UnlockTexture(tex);
        SDL_RenderClear(ren);
        SDL_RenderCopy(ren, tex, NULL, NULL);
        SDL_RenderPresent(ren);
    }

    SDL_DestroyTexture(tex);
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();

    free(cart->prg);
    if (!cart->chr_is_ram) free(cart->chr);
    free(cart);

    return 0;
}