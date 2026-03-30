import pyautogui as pyag
import time as t
import pyperclip as pyclip
pyag.press("super")
pyag.write("Opera GX")
pyag.press("enter")
t.sleep(3.0)
pyag.write("autoclick games")
t.sleep(0.5)
pyag.press("enter")
t.sleep(5.0)
pyag.click(280, 613)
t.sleep(4.5)
pyag.click(210, 535)
t.sleep(5.0)
pyag.click(550, 525)
t.sleep(10.0)
while 1 == 1:
    pyag.tripleClick(450, 450)
