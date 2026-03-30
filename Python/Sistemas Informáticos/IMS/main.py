from classes import Produto
import tkinter as tk
from pydub import AudioSegment
from pydub.playback import play


def mostrar_tudo(produto1, produto2, produto3):
    print(produto1)
    print(produto2)
    print(produto3)


def on_click():
    mostrar_tudo(produto1, produto2, produto3)


produto1 = Produto("Rato gaming", 12, 4, 150)
produto2 = Produto("Placa gráfica", 3, 8, 70)
produto3 = Produto("Auscultadores", 18, 2, 100)

window = tk.Tk()
window.title("IMS")
window.geometry("250x250")
window.resizable(False, False)
icon = tk.PhotoImage(file="icon.png")
window.iconphoto(True, icon)
button = tk.Button(window, text="Calcular IMS",
                   command=on_click).pack(pady=100)
window.mainloop()
