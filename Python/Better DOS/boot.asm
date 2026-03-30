
[org 0x7c00]
bits 16

start:
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7c00

    ; Load 50 sectors for the Mega-Kernel
    mov ah, 0x02    
    mov al, 50      
    mov ch, 0       
    mov dh, 0       
    mov cl, 2       
    mov dl, [boot_drive]
    mov bx, 0x1000  
    int 0x13
    jc disk_error

    jmp 0x0000:0x1000 

disk_error:
    mov ah, 0x0e
    mov al, 'E'
    int 0x10
    jmp $

boot_drive db 0
times 510-($-$$) db 0
dw 0xaa55
