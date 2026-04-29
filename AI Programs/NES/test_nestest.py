"""
Run nestest.nes in automated mode (PC=$C000) and generate a trace log.
Compare against the expected Nintendulator log.
"""
from cartridge import Cartridge
from bus import Bus

cart = Cartridge('nestest.nes')
bus = Bus(cart)
bus.reset()
bus.cpu.pc = 0xC000  # automated test mode
bus.cpu.status = 0x24
bus.cpu.sp = 0xFD
bus.cpu.total_cycles = 7

# Run ~8991 instructions which is the length of the official trace
lines_out = []
for i in range(8991):
    cpu = bus.cpu
    pc = cpu.pc
    op = bus.cpu_read(pc)
    line = f"{pc:04X}  {op:02X}  A:{cpu.a:02X} X:{cpu.x:02X} Y:{cpu.y:02X} P:{cpu.status:02X} SP:{cpu.sp:02X} CYC:{cpu.total_cycles}"
    lines_out.append(line)
    bus.step()
    # Check for failure codes at $02 and $03
    err1 = bus.ram[0x02]
    err2 = bus.ram[0x03]
    if err1 != 0 or err2 != 0:
        print(f"[!] Error codes at step {i}: $02={err1:02X} $03={err2:02X}")
        print("    Last trace:", line)
        break

print(f"Ran {i+1} instructions.")
print(f"Final error codes: $02={bus.ram[0x02]:02X} $03={bus.ram[0x03]:02X}")
print(f"Final CPU cycles: {bus.cpu.total_cycles}")

# Save trace for inspection
with open('my_trace.log', 'w') as f:
    f.write('\n'.join(lines_out))
print(f"Wrote {len(lines_out)} trace lines to my_trace.log")
print("First 5 lines:")
for l in lines_out[:5]:
    print(" ", l)
print("Last 5 lines:")
for l in lines_out[-5:]:
    print(" ", l)
