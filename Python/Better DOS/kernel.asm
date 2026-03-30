
[org 0x1000]
bits 16

kernel_start:
    call clear_screen
    mov si, msg_header
    call print_string
    mov si, msg_welcome
    call print_string

shell_loop:
    mov si, prompt
    call print_string

    mov di, buffer
    call get_input

    mov si, buffer
    cmp byte [si], 0
    je shell_loop

    ; --- Command Dispatcher ---
    
    mov di, cmd_help
    call strcmp
    jc .do_help

    mov di, cmd_ver
    call strcmp
    jc .do_ver

    mov di, cmd_cls
    call strcmp
    jc .do_cls

    mov di, cmd_clear
    call strcmp
    jc .do_cls

    mov di, cmd_color
    call strcmp
    jc .do_color

    mov di, cmd_theme
    call strcmp
    jc .do_theme

    mov di, cmd_time
    call strcmp
    jc .do_time

    mov di, cmd_date
    call strcmp
    jc .do_date

    mov di, cmd_calc
    call strcmp
    jc .do_calc

    mov di, cmd_guess
    call strcmp
    jc .do_guess

    mov di, cmd_timer
    call strcmp
    jc .do_timer

    mov di, cmd_matrix
    call strcmp
    jc .do_matrix

    mov di, cmd_beep
    call strcmp
    jc .do_beep

    mov di, cmd_whoami
    call strcmp
    jc .do_whoami

    mov di, cmd_echo
    call strcmp
    jc .do_echo

    mov di, cmd_about
    call strcmp
    jc .do_about

    mov di, cmd_reboot
    call strcmp
    jc .do_reboot

    mov di, cmd_sys
    call strcmp
    jc .do_sys

    mov di, cmd_pookie
    call strcmp
    jc .do_pookie

    mov di, cmd_halt
    call strcmp
    jc .do_halt

    ; Unknown command
    mov si, msg_unknown
    call print_string
    jmp shell_loop

; --- Commands ---

.do_help:
    mov si, msg_help
    call print_string
    jmp shell_loop

.do_ver:
    mov si, msg_ver
    call print_string
    jmp shell_loop

.do_cls:
    call clear_screen
    jmp shell_loop

.do_color:
    inc byte [text_color]
    and byte [text_color], 0x0F
    jnz .color_set
    mov byte [text_color], 0x07
.color_set:
    mov si, msg_color_changed
    call print_string
    jmp shell_loop

.do_theme:
    xor byte [text_color], 0x08
    mov si, msg_theme_toggle
    call print_string
    jmp shell_loop

.do_time:
    call print_time
    jmp shell_loop

.do_date:
    call print_date
    jmp shell_loop

.do_sys:
    mov si, msg_sys_info
    call print_string
    jmp shell_loop

.do_whoami:
    mov si, msg_root
    call print_string
    jmp shell_loop

.do_echo:
    mov si, msg_echo_prompt
    call print_string
    mov di, buffer
    call get_input
    mov si, buffer
    call print_string
    mov si, newline
    call print_string
    jmp shell_loop

.do_about:
    mov si, msg_about_text
    call print_string
    jmp shell_loop

.do_pookie:
    mov si, msg_pookie
    call print_string
    jmp shell_loop

.do_beep:
    mov ah, 0x0e
    mov al, 0x07
    int 0x10
    jmp shell_loop

.do_reboot:
    mov si, msg_reboot
    call print_string
    mov cx, 5
.reboot_delay:
    call delay
    mov ah, 0x0e
    mov al, '.'
    int 0x10
    loop .reboot_delay
    int 0x19
    jmp $

.do_halt:
    mov si, msg_halted
    call print_string
    hlt
    jmp $

; --- Games & Apps ---

.do_timer:
    mov si, msg_timer_start
    call print_string
    mov cx, 5
.timer_loop:
    mov al, cl
    add al, '0'
    mov ah, 0x0e
    int 0x10
    mov al, ' '
    int 0x10
    call delay
    loop .timer_loop
    mov si, msg_beep_end
    call print_string
    jmp shell_loop

.do_guess:
    mov si, msg_guess_start
    call print_string
.guess_loop:
    mov si, msg_guess_prompt
    call print_string
    mov di, buffer
    call get_input
    mov al, [buffer]
    cmp al, '7'
    je .guess_win
    cmp al, 'q'
    je shell_loop
    mov si, msg_guess_wrong
    call print_string
    jmp .guess_loop
.guess_win:
    mov si, msg_guess_win
    call print_string
    jmp shell_loop

.do_calc:
    mov si, msg_calc_start
    call print_string
    mov si, msg_calc_a
    call print_string
    mov ah, 0x00
    int 0x16
    mov bl, al
    mov ah, 0x0e
    int 0x10
    mov si, newline
    call print_string
    mov si, msg_calc_b
    call print_string
    mov ah, 0x00
    int 0x16
    mov bh, al
    mov ah, 0x0e
    int 0x10
    mov si, newline
    call print_string
    sub bl, '0'
    sub bh, '0'
    add bl, bh
    add bl, '0'
    mov si, msg_calc_res
    call print_string
    mov ah, 0x0e
    mov al, bl
    int 0x10
    mov si, newline
    call print_string
    jmp shell_loop

.do_matrix:
    call clear_screen
    mov byte [text_color], 0x02
    mov dx, 2000
.matrix_loop:
    mov ah, 0x00
    int 0x1a
    mov al, dl
    and al, 0x3F
    add al, '!'
    mov ah, 0x0e
    int 0x10
    dec dx
    jnz .matrix_loop
    mov byte [text_color], 0x0E
    jmp shell_loop

; --- Functions ---

delay:
    pusha
    mov ax, 0
    mov ah, 0x86
    mov cx, 0x0007
    mov dx, 0xA120
    int 0x15
    popa
    ret

clear_screen:
    mov ax, 0x0003
    int 0x10
    ret

print_string:
    lodsb
    or al, al
    jz .done
    mov ah, 0x0e
    mov bh, 0
    mov bl, [text_color]
    int 0x10
    jmp print_string
.done:
    ret

print_time:
    mov si, msg_time_lbl
    call print_string
    mov ah, 0x02
    int 0x1a
    mov al, ch
    call print_bcd
    mov al, ':'
    mov ah, 0x0e
    int 0x10
    mov al, cl
    call print_bcd
    mov si, newline
    call print_string
    ret

print_date:
    mov si, msg_date_lbl
    call print_string
    mov ah, 0x04
    int 0x1a
    mov al, dl
    call print_bcd
    mov al, '/'
    mov ah, 0x0e
    int 0x10
    mov al, dh
    call print_bcd
    mov al, '/'
    mov ah, 0x0e
    int 0x10
    mov al, cl
    call print_bcd
    mov si, newline
    call print_string
    ret

print_bcd:
    push ax
    shr al, 4
    add al, '0'
    mov ah, 0x0e
    int 0x10
    pop ax
    and al, 0x0f
    add al, '0'
    mov ah, 0x0e
    int 0x10
    ret

get_input:
    xor cl, cl
.loop:
    mov ah, 0x00
    int 0x16
    cmp al, 13
    je .done
    cmp al, 8
    je .backspace
    cmp cl, 31
    je .loop
    mov ah, 0x0e
    int 0x10
    stosb
    inc cl
    jmp .loop
.backspace:
    cmp cl, 0
    je .loop
    dec cl
    dec di
    mov ah, 0x0e
    mov al, 8
    int 0x10
    mov al, ' '
    int 0x10
    mov al, 8
    int 0x10
    jmp .loop
.done:
    mov al, 0
    stosb
    mov si, newline
    call print_string
    ret

strcmp:
    push si
    push di
.loop:
    mov al, [si]
    mov bl, [di]
    cmp al, bl
    jne .not_equal
    or al, al
    jz .equal
    inc si
    inc di
    jmp .loop
.not_equal:
    pop di
    pop si
    clc
    ret
.equal:
    pop di
    pop si
    stc
    ret

; --- Data ---
text_color  db 0x0E
newline     db 13, 10, 0
msg_header  db '  _____             _    _         ', 13, 10
            db ' |  __ \           | |  (_)        ', 13, 10
            db ' | |__) |__   ___  | | ___  ___    ', 13, 10
            db ' |  ___/ _ \ / _ \ | |/ / |/ _ \   ', 13, 10
            db ' | |  | (_) | (_) ||   <| |  __/   ', 13, 10
            db ' |_|   \___/ \___/ |_|\_\_|\___|   ', 13, 10, 0

msg_welcome db 13, 10, 'POOKIE-OS MEGA v4.0.2', 13, 10, 'Ready for anything! Type "help".', 13, 10, 0
prompt      db 'POOKIE:\> ', 0
msg_unknown db 'Command Unknown. Try "help".', 13, 10, 0
msg_help    db 'SYSTEM: ver, cls, color, theme, sys, whoami, reboot, halt', 13, 10
            db 'APPS  : time, date, calc, guess, timer, matrix, echo, beep, about', 13, 10, 0

msg_ver     db 'POOKIE-OS MEGA [v4.0.2]', 13, 10, 0
msg_sys_info db 'Arch: x86 Real Mode', 13, 10, 'Mem : 1.44MB Floppy Image', 13, 10, 0
msg_about_text db 'POOKIE-OS was built for maximum fun and learning.', 13, 10, 'A tiny kernel with huge potential.', 13, 10, 0
msg_root    db 'Current User: Administrator (Root)', 13, 10, 0
msg_echo_prompt db 'Enter text to repeat: ', 0
msg_timer_start db 'Countdown initiated: ', 0
msg_beep_end    db 'BEEP! Time up!', 13, 10, 0
msg_reboot  db 'Restarting system', 0
msg_halted  db 'Kernel Shutdown.', 13, 10, 0
msg_color_changed db 'Color shifted.', 13, 10, 0
msg_theme_toggle db 'Theme intensity toggled.', 13, 10, 0
msg_pookie  db 'Pookie mode: ACTIVE', 13, 10, 0

msg_time_lbl db 'Current Time: ', 0
msg_date_lbl db 'Current Date: ', 0

msg_guess_start db 'Guess 0-9 (q to exit)', 13, 10, 0
msg_guess_prompt db 'Guess: ', 0
msg_guess_win   db 'YOU GOT IT!', 13, 10, 0
msg_guess_wrong db ' Nope.', 13, 10, 0

msg_calc_start db 'Addition Mode:', 13, 10, 0
msg_calc_a     db 'A: ', 0
msg_calc_b     db 'B: ', 0
msg_calc_res   db 'Result: ', 0

cmd_help    db 'help', 0
cmd_ver     db 'ver', 0
cmd_cls     db 'cls', 0
cmd_clear   db 'clear', 0
cmd_color   db 'color', 0
cmd_theme   db 'theme', 0
cmd_time    db 'time', 0
cmd_date    db 'date', 0
cmd_sys     db 'sys', 0
cmd_pookie  db 'pookie', 0
cmd_calc    db 'calc', 0
cmd_guess   db 'guess', 0
cmd_timer   db 'timer', 0
cmd_matrix  db 'matrix', 0
cmd_beep    db 'beep', 0
cmd_echo    db 'echo', 0
cmd_about   db 'about', 0
cmd_whoami  db 'whoami', 0
cmd_reboot  db 'reboot', 0
cmd_halt    db 'halt', 0

buffer      times 32 db 0

times 25600-($-$$) db 0
