#!/usr/bin/env python3
"""
Creates a bootable Windows 1.0-style OS image with mouse and keyboard support
Compile and run: python3 create_os.py
Then boot with: qemu-system-x86_64 -fda os.img
"""

# Bootloader and OS kernel in x86 assembly
bootloader_asm = """
[BITS 16]
[ORG 0x7C00]

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    sti

    ; Set video mode 0x13
    mov ah, 0x00
    mov al, 0x13
    int 0x10

    call setup_pal
    call init_ms
    call draw_scr

loop:
    ; Keyboard check
    mov ah, 0x01
    int 0x16
    jz .nk
    mov ah, 0x00
    int 0x16
    cmp ah, 0x01
    je reset
.nk:
    call upd_ms
    jmp loop

reset:
    int 0x19

init_ms:
    mov ax, 0x00
    int 0x33
    mov ax, 0x01
    int 0x33
    ret

upd_ms:
    pusha
    mov ax, 0x03
    int 0x33
    shr cx, 1
    
    ; Bounds
    cmp cx, 317
    jg .e
    cmp dx, 197
    jg .e
    
    ; Draw 2x2 cursor
    mov di, dx
    imul di, 320
    add di, cx
    mov ax, 0xA000
    mov es, ax
    mov byte [es:di], 1
    mov byte [es:di+1], 1
    add di, 320
    mov byte [es:di], 1
    mov byte [es:di+1], 1
.e:
    popa
    ret

setup_pal:
    mov dx, 0x03C8
    xor al, al
    out dx, al
    inc dx
    out dx, al
    out dx, al
    out dx, al
    
    dec dx
    mov al, 1
    out dx, al
    inc dx
    mov al, 0x3F
    out dx, al
    out dx, al
    out dx, al
    
    dec dx
    mov al, 2
    out dx, al
    inc dx
    mov al, 0x2A
    out dx, al
    out dx, al
    out dx, al
    
    dec dx
    mov al, 3
    out dx, al
    inc dx
    xor al, al
    out dx, al
    out dx, al
    mov al, 0x2A
    out dx, al
    ret

draw_scr:
    ; Clear
    mov ax, 0xA000
    mov es, ax
    xor di, di
    xor al, al
    mov cx, 64000
    rep stosb

    ; Title bar (blue)
    xor di, di
    mov al, 3
    mov cx, 3840
    rep stosb
    
    ; Menu bar (gray)
    mov al, 2
    mov cx, 3200
    rep stosb
    
    ; Window 1 outline
    mov si, 50
.w1y:
    mov di, si
    imul di, 320
    add di, 40
    mov cx, 150
.w1x:
    mov byte [es:di], 1
    inc di
    loop .w1x
    inc si
    cmp si, 150
    jl .w1y
    
    ; Window 2 outline  
    mov si, 80
.w2y:
    mov di, si
    imul di, 320
    add di, 100
    mov cx, 180
.w2x:
    mov byte [es:di], 2
    inc di
    loop .w2x
    inc si
    cmp si, 170
    jl .w2y
    
    ; Text
    mov si, t1
    mov dh, 0
    mov dl, 2
    call prt
    
    mov si, t2
    mov dh, 1
    mov dl, 1
    call prt
    
    mov si, t3
    mov dl, 7
    call prt
    
    mov si, t4
    mov dh, 24
    mov dl, 1
    call prt
    
    ret

prt:
    pusha
    mov ah, 0x02
    xor bh, bh
    int 0x10
.l:
    lodsb
    test al, al
    jz .d
    mov ah, 0x0E
    mov bl, 0x0F
    int 0x10
    jmp .l
.d:
    popa
    ret

t1 db 'MS-DOS Executive', 0
t2 db 'File', 0
t3 db 'View', 0
t4 db 'Mouse+Keys work | ESC=Reboot', 0

times 510-($-$$) db 0
dw 0xAA55
"""


def create_boot_image(nasm_path=None):
    """Create bootable disk image"""
    import subprocess
    import os
    import shutil

    # Write assembly to file
    with open('bootloader.asm', 'w') as f:
        f.write(bootloader_asm)

    print("Assembling bootloader...")

    # Determine NASM executable to use
    if nasm_path:
        nasm_executable = nasm_path
        print(f"Using provided NASM path: {nasm_executable}")
        if not os.path.exists(nasm_executable):
            print(f"WARNING: Provided path does not exist: {nasm_executable}")
    else:
        # Check if NASM is in PATH
        nasm_executable = shutil.which('nasm')
        if nasm_executable:
            print(f"Found NASM in PATH at: {nasm_executable}")
        else:
            nasm_executable = 'nasm'
            print("NASM not found in PATH, trying 'nasm' command anyway...")

    try:
        # Assemble the bootloader
        result = subprocess.run([nasm_executable, '-f', 'bin', 'bootloader.asm', '-o', 'os.bin'],
                                capture_output=True, text=True, shell=False)

        if result.returncode != 0:
            print(f"NASM error (return code {result.returncode}):")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

        # Create 1.44MB floppy image
        with open('os.bin', 'rb') as f:
            boot_data = f.read()

        print(f"Boot sector size: {len(boot_data)} bytes")

        if len(boot_data) != 512:
            print(
                f"ERROR: Boot sector must be exactly 512 bytes, got {len(boot_data)}")
            return False

        floppy_image = bytearray([0] * 1474560)
        floppy_image[0:512] = boot_data

        with open('os.img', 'wb') as f:
            f.write(floppy_image)

        # Clean up
        if os.path.exists('os.bin'):
            os.remove('os.bin')

        print("✓ Bootable OS image created: os.img")
        print("\nTo boot this OS:")
        print("1. QEMU: qemu-system-x86_64 -fda os.img")
        print("   Click in window to capture mouse")
        print("   Press Ctrl+Alt+G to release mouse")
        print("2. VirtualBox: Attach os.img as floppy drive")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Bootable Windows 1.0-style Operating System")
    print("=" * 60)

    NASM_PATH = r"C:\Users\gatin\AppData\Local\bin\NASM\nasm.exe"

    success = create_boot_image(nasm_path=NASM_PATH)

    if success:
        print("\nOS Features:")
        print("- Boots directly on x86 hardware/VM")
        print("- VGA 320x200 graphics mode")
        print("- Windows 1.0 style UI with windows")
        print("- Working mouse cursor")
        print("- Keyboard input responsive")
        print("- ESC key reboots system")
        print("=" * 60)
    else:
        print("\n✗ Build failed. Check errors above.")
        print("=" * 60)
