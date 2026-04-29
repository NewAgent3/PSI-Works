"""
NES Controller (standard joypad). Buttons ordered: A, B, Select, Start, Up, Down, Left, Right.
"""


class Controller:
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_SELECT = 2
    BUTTON_START = 3
    BUTTON_UP = 4
    BUTTON_DOWN = 5
    BUTTON_LEFT = 6
    BUTTON_RIGHT = 7

    def __init__(self):
        self.buttons = 0        # 8-bit: bit0=A, bit1=B, ...
        self.strobe = 0
        self.shift = 0

    def set_button(self, index, pressed):
        if pressed:
            self.buttons |= (1 << index)
        else:
            self.buttons &= ~(1 << index)

    def write(self, value):
        self.strobe = value & 1
        if self.strobe:
            self.shift = self.buttons

    def read(self):
        if self.strobe:
            return self.buttons & 1
        bit = self.shift & 1
        self.shift = (self.shift >> 1) | 0x80
        return bit
