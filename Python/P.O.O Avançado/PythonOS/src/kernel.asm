; =============================================================================
;  Win2K-OS  — Kernel
;  Implements a Windows 2000-styled text-mode desktop
;
;  Layout (80×25 text mode, 16 colours):
;    Row  0       : title bar  (bright-white on blue,  0x1F)
;    Rows 1–22   : desktop     (white on blue,          0x17)
;    Row 23       : status bar  (black on cyan,          0x30)
;    Row 24       : taskbar     (black on gray,          0x70)
;
;  Colour attributes quick-ref (bg<<4 | fg)
;    0x17 = white on blue        (desktop)
;    0x1F = bright-white on blue (title / selected)
;    0x70 = black on light-gray  (taskbar)
;    0x4F = bright-white on red  (close btn)
;    0x2F = bright-white on green(start btn)
;    0x30 = black on cyan        (status bar)
;    0x07 = light-gray on black  (normal window body)
;    0x0F = bright-white on black(window highlight)
;    0x78 = bright-white on gray (window title)
; =============================================================================

[BITS 16]
[ORG 0x8000]

; ---------- VGA text mode constants ----------
VGA_SEG     equ 0xB800
COLS        equ 80
ROWS        equ 25

; colour attributes
COL_DESKTOP equ 0x17      ; white on blue
COL_TITLE   equ 0x1F      ; bright-white on blue
COL_TASKBAR equ 0x70      ; black on light-gray
COL_START   equ 0x2A      ; bright-green on green  → will override to look like btn
COL_STATUS  equ 0x30      ; black on cyan
COL_WBODY   equ 0x07      ; gray on black
COL_WTITLE  equ 0x17      ; white on blue  (window title bar)
COL_CLOSE   equ 0x4F      ; bright-white on red
COL_WINSEL  equ 0x78      ; dark-gray on light-gray (window chrome)

kernel_main:
    ; set up segments
    mov ax, 0x0000
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7BFE

    ; ---- set video mode 3 (80×25 colour text) ----
    mov ax, 0x0003
    int 0x10

    ; ---- hide cursor ----
    mov ah, 0x01
    mov ch, 0x3F
    int 0x10

    ; ---- build the desktop ----
    call draw_desktop
    call draw_titlebar
    call draw_taskbar
    call draw_statusbar

    ; ---- draw sample windows ----
    ; My Computer window  (col 2, row 2, width 34, height 12)
    mov cl, 2
    mov ch, 2
    mov dl, 34
    mov dh, 12
    call draw_window
    mov si, str_mycomp
    mov cl, 4
    mov ch, 2
    call draw_wintitle

    ; content inside My Computer
    mov cl, 4    ; x
    mov ch, 4    ; y
    mov si, str_hdd
    call draw_string_attr
    mov ch, 5
    mov si, str_floppy
    call draw_string_attr
    mov ch, 6
    mov si, str_cdrom
    call draw_string_attr
    mov ch, 7
    mov si, str_netplace
    call draw_string_attr
    mov ch, 9
    mov si, str_status_mycomp
    call draw_string_attr

    ; Notepad window  (col 43, row 3, width 35, height 14)
    mov cl, 43
    mov ch, 3
    mov dl, 35
    mov dh, 14
    call draw_window
    mov si, str_notepad
    mov cl, 45
    mov ch, 3
    call draw_wintitle

    ; notepad content
    mov cl, 45
    mov ch, 5
    mov si, str_np1
    call draw_string_attr
    mov ch, 6
    mov si, str_np2
    call draw_string_attr
    mov ch, 7
    mov si, str_np3
    call draw_string_attr
    mov ch, 8
    mov si, str_np4
    call draw_string_attr
    mov ch, 9
    mov si, str_np5
    call draw_string_attr
    mov ch, 10
    mov si, str_np6
    call draw_string_attr

    ; ---- draw desktop icons ----
    call draw_icons

    ; ---- draw start button ----
    call draw_start_btn

    ; ---- draw clock ----
    call update_clock

    ; ---- keyboard event loop ----
.event_loop:
    ; update clock every pass
    call update_clock

    ; poll for keypress (non-blocking)
    mov ah, 0x01
    int 0x16
    jz .event_loop       ; no key yet

    mov ah, 0x00
    int 0x16              ; consume key
    ; AL = ASCII char, AH = scan code

    ; ESC (scan 0x01) = print "Shutting down..."
    cmp ah, 0x01
    je .shutdown

    jmp .event_loop

.shutdown:
    ; draw shutdown screen
    call draw_shutdown
    jmp .halt

.halt:
    cli
    hlt
    jmp .halt


; =============================================================================
;  draw_desktop — fill rows 1–22 with blue desktop
; =============================================================================
draw_desktop:
    push es
    mov ax, VGA_SEG
    mov es, ax

    mov cx, COLS * (ROWS - 3)   ; rows 1-22 → 22 rows, but we do 1..22 = 22
    ; actually rows 0..24: row0=title, 1-22=desktop, 23=status, 24=taskbar
    ; fill rows 1..22 = 22 rows
    ; offset for row 1 = 80*1*2 = 160
    mov di, 160
.fill:
    mov word [es:di], (COL_DESKTOP << 8) | 0x20   ; space with desktop colour
    add di, 2
    loop .fill

    pop es
    ret

; =============================================================================
;  draw_titlebar — row 0: "Win2K-OS  -  Professional Edition"
; =============================================================================
draw_titlebar:
    push es
    mov ax, VGA_SEG
    mov es, ax

    ; fill row 0 with title colour + spaces
    mov di, 0
    mov cx, COLS
.fill:
    mov word [es:di], (COL_TITLE << 8) | 0x20
    add di, 2
    loop .fill

    ; print title string centred
    mov si, str_os_title
    mov cx, 0            ; row 0
    mov cl, 0
    push cx
    ; calculate centre position
    ; length of str_os_title = 36 chars → start col = (80-36)/2 = 22
    mov cl, 22
    mov ch, 0
    call set_cursor_vga
    mov si, str_os_title
    mov bl, COL_TITLE
    call vga_print

    pop cx
    pop es
    ret

; =============================================================================
;  draw_taskbar — row 24: taskbar with clock area
; =============================================================================
draw_taskbar:
    push es
    mov ax, VGA_SEG
    mov es, ax

    ; row 24, offset = 80*24*2 = 3840
    mov di, 3840
    mov cx, COLS
.fill:
    mov word [es:di], (COL_TASKBAR << 8) | 0x20
    add di, 2
    loop .fill

    pop es
    ret

; =============================================================================
;  draw_statusbar — row 23: status hints
; =============================================================================
draw_statusbar:
    push es
    mov ax, VGA_SEG
    mov es, ax

    ; row 23, offset = 80*23*2 = 3680
    mov di, 3680
    mov cx, COLS
.fill:
    mov word [es:di], (COL_STATUS << 8) | 0x20
    add di, 2
    loop .fill

    ; print status text
    mov cl, 2
    mov ch, 23
    call set_cursor_vga
    mov si, str_statusbar
    mov bl, COL_STATUS
    call vga_print

    pop es
    ret

; =============================================================================
;  draw_start_btn — draws "[▶ Start]" at left side of taskbar
; =============================================================================
draw_start_btn:
    push es
    mov ax, VGA_SEG
    mov es, ax

    ; position: row 24, col 1
    mov di, 3840 + 1*2
    mov si, str_start_btn
    mov bl, 0x2F          ; bright-white on green

.loop:
    lodsb
    test al, al
    jz .done
    mov ah, bl
    mov word [es:di], ax
    add di, 2
    jmp .loop
.done:
    pop es
    ret

; =============================================================================
;  draw_window — draw a simple 3D-style window border
;    CL = left col, CH = top row, DL = width, DH = height
; =============================================================================
draw_window:
    pusha
    push es
    mov ax, VGA_SEG
    mov es, ax

    ; save params
    mov [win_x], cl
    mov [win_y], ch
    mov [win_w], dl
    mov [win_h], dh

    ; --- fill interior with light-gray/white on gray ---
    mov al, [win_y]
    mov ah, 0
    mov bx, ax
    ; start from row win_y+1
    inc al
    mov [tmp_row], al

.fill_interior:
    mov al, [tmp_row]
    mov bl, [win_y]
    add bl, [win_h]
    cmp al, bl
    jge .done_fill

    mov cl, [win_x]
    inc cl                    ; col win_x+1
    mov bh, cl
    add bh, [win_w]
    dec bh                    ; col win_x+win_w-1

.fill_row:
    cmp cl, bh
    jge .next_row
    mov ch, al
    call set_cursor_vga
    mov ax, (0x17 << 8) | 0x20   ; white on blue interior (will be overdrawn)
    ; actually use light gray on gray for window body
    mov ax, (0x78 << 8) | 0x20   ; dark on gray
    push es
    mov bx, VGA_SEG
    mov es, bx
    ; compute DI
    push ax
    xor ax, ax
    mov al, ch          ; row
    mov bl, COLS
    mul bl
    xor bh, bh
    mov bl, cl          ; col
    add ax, bx
    shl ax, 1
    mov di, ax
    pop ax
    mov word [es:di], ax
    pop es
    inc cl
    jmp .fill_row

.next_row:
    inc byte [tmp_row]
    jmp .fill_interior

.done_fill:
    ; --- draw title bar row (row win_y) ---
    mov cl, [win_x]
    mov ch, [win_y]
    call set_cursor_vga
    mov bx, VGA_SEG
    mov es, bx
    xor ax, ax
    mov al, [win_y]
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, [win_x]
    add ax, bx
    shl ax, 1
    mov di, ax

    ; fill title bar
    xor bx, bx
    mov bl, [win_w]
    mov cx, bx
    mov ah, COL_WTITLE
.tbar_fill:
    mov al, 0x20
    mov word [es:di], ax
    add di, 2
    loop .tbar_fill

    ; draw close button at right of title bar  [X]
    ; position: win_x + win_w - 4
    mov cl, [win_x]
    add cl, [win_w]
    sub cl, 4
    mov ch, [win_y]
    xor ax, ax
    mov al, [win_y]
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, cl
    add ax, bx
    shl ax, 1
    mov di, ax
    mov word [es:di], (COL_CLOSE << 8) | '['
    add di, 2
    mov word [es:di], (COL_CLOSE << 8) | 'X'
    add di, 2
    mov word [es:di], (COL_CLOSE << 8) | ']'

    ; --- draw outer border ---
    ; top-left corner
    mov cl, [win_x]
    mov ch, [win_y]
    xor ax, ax
    mov al, ch
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, cl
    add ax, bx
    shl ax, 1
    mov di, ax
    mov word [es:di], (COL_WINSEL << 8) | 0xC9   ; ╔

    ; top edge
    mov cx, [win_w]
    sub cx, 2
    add di, 2
.top_edge:
    mov word [es:di], (COL_WINSEL << 8) | 0xCD   ; ═
    add di, 2
    loop .top_edge

    ; top-right corner
    mov word [es:di], (COL_WINSEL << 8) | 0xBB   ; ╗

    ; left & right edges
    mov al, [win_y]
    inc al
    mov [tmp_row], al
.side_edges:
    mov al, [tmp_row]
    mov bl, [win_y]
    add bl, [win_h]
    cmp al, bl
    jge .bottom_border

    ; left edge
    xor ah, ah
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, [win_x]
    add ax, bx
    shl ax, 1
    mov di, ax
    mov word [es:di], (COL_WINSEL << 8) | 0xBA   ; ║

    ; right edge
    xor ax, ax
    mov al, [tmp_row]
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, [win_x]
    add bl, [win_w]
    dec bl
    add ax, bx
    shl ax, 1
    mov di, ax
    mov word [es:di], (COL_WINSEL << 8) | 0xBA   ; ║

    inc byte [tmp_row]
    jmp .side_edges

.bottom_border:
    ; bottom row
    mov al, [win_y]
    add al, [win_h]
    xor ah, ah
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, [win_x]
    add ax, bx
    shl ax, 1
    mov di, ax
    mov word [es:di], (COL_WINSEL << 8) | 0xC8   ; ╚

    mov cx, [win_w]
    sub cx, 2
    add di, 2
.bot_edge:
    mov word [es:di], (COL_WINSEL << 8) | 0xCD   ; ═
    add di, 2
    loop .bot_edge
    mov word [es:di], (COL_WINSEL << 8) | 0xBC   ; ╝

    pop es
    popa
    ret

; =============================================================================
;  draw_wintitle — write title text into window title bar
;    SI = string, CL = col, CH = row
; =============================================================================
draw_wintitle:
    pusha
    push es
    mov ax, VGA_SEG
    mov es, ax

    xor ax, ax
    mov al, ch
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, cl
    add ax, bx
    shl ax, 1
    mov di, ax

    mov ah, COL_TITLE
.loop:
    lodsb
    test al, al
    jz .done
    mov word [es:di], ax
    add di, 2
    jmp .loop
.done:
    pop es
    popa
    ret

; =============================================================================
;  draw_string_attr — write a string with attribute 0x78 (desktop-ish)
;    SI = string, CL = col, CH = row
; =============================================================================
draw_string_attr:
    pusha
    push es
    mov ax, VGA_SEG
    mov es, ax

    xor ax, ax
    mov al, ch
    mul byte [COLS_CONST]
    xor bh, bh
    mov bl, cl
    add ax, bx
    shl ax, 1
    mov di, ax

    mov ah, 0x78      ; dark text on gray (window body)
.loop:
    lodsb
    test al, al
    jz .done
    mov word [es:di], ax
    add di, 2
    jmp .loop
.done:
    pop es
    popa
    ret

; =============================================================================
;  draw_icons — draw desktop icons on the blue desktop
; =============================================================================
draw_icons:
    pusha
    push es
    mov ax, VGA_SEG
    mov es, ax

    ; Icon 1: My Computer  (col 1, row 2)
    mov cl, 1 
    mov ch, 2
    call set_cursor_vga
    mov si, str_icon_cpu
    mov bl, COL_TITLE
    call vga_print

    mov cl, 1
    mov ch, 3
    call set_cursor_vga
    mov si, str_icon_mycomp
    mov bl, COL_TITLE
    call vga_print

    ; Icon 2: Recycle Bin  (col 1, row 5)
    mov cl, 1
    mov ch, 5
    call set_cursor_vga
    mov si, str_icon_recycle
    mov bl, COL_TITLE
    call vga_print

    mov cl, 1
    mov ch, 6
    call set_cursor_vga
    mov si, str_icon_bin
    mov bl, COL_TITLE
    call vga_print

    ; Icon 3: Network  (col 1, row 8)
    mov cl, 1
    mov ch, 8
    call set_cursor_vga
    mov si, str_icon_net
    mov bl, COL_TITLE
    call vga_print

    mov cl, 1
    mov ch, 9
    call set_cursor_vga
    mov si, str_icon_netname
    mov bl, COL_TITLE
    call vga_print

    ; Icon 4: Documents (col 1, row 11)
    mov cl, 1
    mov ch, 11
    call set_cursor_vga
    mov si, str_icon_doc
    mov bl, COL_TITLE
    call vga_print

    mov cl, 1
    mov ch, 12
    call set_cursor_vga
    mov si, str_icon_docname
    mov bl, COL_TITLE
    call vga_print

    pop es
    popa
    ret

; =============================================================================
;  update_clock — read BIOS RTC and display at row 24 col 70
; =============================================================================
update_clock:
    pusha
    push es

    mov ah, 0x02          ; BIOS RTC get time
    int 0x1A
    ; CH = hours BCD, CL = minutes BCD, DH = seconds BCD

    ; convert hours to ASCII
    mov al, ch
    call bcd_to_ascii
    mov [clock_h1], ah
    mov [clock_h2], al

    mov al, cl
    call bcd_to_ascii
    mov [clock_m1], ah
    mov [clock_m2], al

    mov al, dh
    call bcd_to_ascii
    mov [clock_s1], ah
    mov [clock_s2], al

    ; print at row 24, col 69  (11 chars: "HH:MM:SS AM")
    mov ax, VGA_SEG
    mov es, ax

    ; offset = (24*80 + 68)*2 = (1920+68)*2 = 1988*2 = 3976
    mov di, 3976

    mov si, clock_str
    mov ah, 0x70          ; taskbar colour
.loop:
    lodsb
    test al, al
    jz .done
    mov word [es:di], ax
    add di, 2
    jmp .loop
.done:
    pop es
    popa
    ret

; BCD byte in AL → high nibble digit in AH, low nibble digit in AL
bcd_to_ascii:
    mov ah, al
    shr ah, 4
    and al, 0x0F
    add ax, 0x3030
    ret

; =============================================================================
;  draw_shutdown — render a blue screen (ctrl+alt+del style)
; =============================================================================
draw_shutdown:
    push es
    mov ax, VGA_SEG
    mov es, ax
    ; fill entire screen dark blue + bright white text
    mov cx, COLS * ROWS
    xor di, di
.fill:
    mov word [es:di], (0x17 << 8) | 0x20
    add di, 2
    loop .fill

    ; print shutdown message
    mov cl, 20
    mov ch, 10
    call set_cursor_vga
    mov si, str_shutdown
    mov bl, 0x17
    call vga_print

    mov cl, 22
    mov ch, 12
    call set_cursor_vga
    mov si, str_shutdown2
    mov bl, 0x17
    call vga_print

    pop es
    ret

; =============================================================================
;  Utility: set_cursor_vga
;    CL = column, CH = row
;    Computes DI = (row*80 + col)*2  (for ES = VGA_SEG)
; =============================================================================
set_cursor_vga:
    ; also move BIOS cursor so vga_print knows where to write
    push ax
    push bx
    push dx
    mov ah, 0x02
    xor bh, bh
    mov dh, ch
    mov dl, cl
    int 0x10
    pop dx
    pop bx
    pop ax
    ret

; =============================================================================
;  Utility: vga_print — print string SI at current cursor using attribute BL
;    Advances cursor per character
; =============================================================================
vga_print:
    push es
    push ax
    push di
    mov ax, VGA_SEG
    mov es, ax

.loop:
    lodsb
    test al, al
    jz .done

    ; get cursor position
    push bx
    mov ah, 0x03
    xor bh, bh
    int 0x10            ; DH=row, DL=col
    pop bx

    ; compute di
    push ax
    xor ax, ax
    mov al, dh
    mul byte [COLS_CONST]
    xor ah, ah
    add al, dl
    adc ah, 0
    shl ax, 1
    mov di, ax
    pop ax

    mov ah, bl
    mov word [es:di], ax

    ; advance cursor
    push bx
    inc dl
    cmp dl, COLS
    jl .no_wrap
    xor dl, dl
    inc dh
.no_wrap:
    mov ah, 0x02
    xor bh, bh
    int 0x10
    pop bx
    jmp .loop
.done:
    pop di
    pop ax
    pop es
    ret

; =============================================================================
;  Data
; =============================================================================
COLS_CONST  db 80

; window scratch vars
win_x   db 0
win_y   db 0
win_w   db 0
win_h   db 0
tmp_row db 0

str_os_title    db '  Win2K-OS  Professional Edition  v1.0  ', 0

str_start_btn   db ' Start ', 0

str_statusbar   db ' ESC = Shutdown   |   Win2K-OS Professional Edition   |   NASM Kernel  ', 0

str_mycomp      db ' My Computer ', 0
str_hdd         db ' [C:]  Local Disk (C:)  4.00 GB ', 0
str_floppy      db ' [A:]  3.5" Floppy Disk          ', 0
str_cdrom       db ' [D:]  CD-ROM Drive              ', 0
str_netplace    db ' [Z:]  Network Drive             ', 0
str_status_mycomp db '  4 object(s)                    ', 0

str_notepad     db ' Notepad - [welcome.txt] ', 0
str_np1         db ' ================================ ', 0
str_np2         db '  Welcome to Win2K-OS!            ', 0
str_np3         db '  A homebrew OS inspired by       ', 0
str_np4         db '  Windows 2000 Professional.      ', 0
str_np5         db '  Written in NASM Assembly.       ', 0
str_np6         db ' ================================ ', 0

; desktop icons
str_icon_cpu    db '  [=]  ', 0
str_icon_mycomp db ' My PC ', 0

str_icon_recycle db '  [o]  ', 0
str_icon_bin    db '  Bin  ', 0

str_icon_net    db '  [-]  ', 0
str_icon_netname db ' NetNbr', 0

str_icon_doc    db '  [#]  ', 0
str_icon_docname db '  Docs ', 0

str_shutdown    db '  Windows 2000 is shutting down...  ', 0
str_shutdown2   db '  It is now safe to turn off your computer.  ', 0

; clock string (updated by update_clock)
clock_str:
  db ' '
clock_h1 db '0'
clock_h2 db '0'
  db ':'
clock_m1 db '0'
clock_m2 db '0'
  db ':'
clock_s1 db '0'
clock_s2 db '0'
  db ' ', 0
