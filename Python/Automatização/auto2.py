import pyautogui as pyag
import time as t
import pyperclip as pyclip
pyag.press("super")
pyag.write("Bloco de Notas")
pyag.press("enter")
t.sleep(1.0)
pyclip.copy("Escola Secundária Cacilhas-Tejo")
pyag.hotkey("ctrl", "v")
