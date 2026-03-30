import tkinter as tk
from tkinter import messagebox


def soma():
    numero1 = num1.get()
    numero2 = num2.get()
    if numero1 == '' or numero2 == '':
        resultado.config(text="")
        messagebox.showerror(
            "ERRO", message="Tem de introduzir valores nos campos")
    else:
        numero1 = float(num1.get())
        numero2 = float(num2.get())
        conta = numero1 + numero2
        resultado.config(text=f"O resultado é {conta}")


window = tk.Tk()
window.title("SOMA")
window.geometry("300x300")
window.resizable(False, False)
titulo = tk.Label(window, text="SOMA", fg="blue",
                  font=("Arial", 30, "normal"))
titulo.pack(pady="5")
image1 = tk.PhotoImage(file="icon.png")
label_image = tk.Label(image=image1)
label_image.pack(pady="0")
texto = tk.Label(window, text="Introduza o 1º número")
texto.pack(pady="5")
num1 = tk.Entry(window)
num1.pack(pady="5")
texto2 = tk.Label(window, text="Introduza o 2º número")
texto2.pack(pady="5")
num2 = tk.Entry(window)
num2.pack(pady="5")
resultado = tk.Label(window)
resultado.pack(pady="5")
click = tk.Button(window, text="Calcular Soma", command=(soma))
click.pack(side="bottom", pady="5")
window.mainloop()
