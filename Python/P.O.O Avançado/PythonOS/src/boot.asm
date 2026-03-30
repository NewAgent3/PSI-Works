; =============================================================================
;  Win2K-OS Bootloader
;  Loads the kernel from disk and jumps to it
; =============================================================================
[BITS 16]
[ORG 0x7C00]

KERNEL_LOAD_SEG  equ 0x0000
KERNEL_LOAD_OFF  equ 0x8000
KERNEL_SECTORS   equ 40          ; how many sectors to load

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov sp, 0x7BFE
    sti

    mov [boot_drive], dl         ; save BIOS boot drive

    ; ---------- print loading message ----------
    mov si, msg_loading
    call print_str

    ; ---------- load kernel ----------
    mov ah, 0x02
    mov al, KERNEL_SECTORS
    mov ch, 0                    ; cylinder 0
    mov cl, 2                    ; start at sector 2
    mov dh, 0                    ; head 0
    mov dl, [boot_drive]
    mov bx, KERNEL_LOAD_OFF
    int 0x13
    jnc .loaded

    ; read error
    mov si, msg_error
    call print_str
    jmp hang

.loaded:
    mov si, msg_ok
    call print_str
    jmp KERNEL_LOAD_SEG:KERNEL_LOAD_OFF

; ---------- helpers ----------
print_str:
    pusha
.loop:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0E
    mov bh, 0
    int 0x10
    jmp .loop
.done:
    popa
    ret

hang:
    cli
    hlt
    jmp hang

; ---------- data ----------
boot_drive  db 0
msg_loading db 'Win2K-OS: Loading kernel...', 0x0D, 0x0A, 0
msg_ok      db 'OK. Jumping to kernel.', 0x0D, 0x0A, 0
msg_error   db 'DISK READ ERROR!', 0x0D, 0x0A, 0

times 510-($-$$) db 0
dw 0xAA55
