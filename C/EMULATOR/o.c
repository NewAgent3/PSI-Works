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
                    cpu.f &= ~(FLAG_Z | FLAG_N | FLAG_H);
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