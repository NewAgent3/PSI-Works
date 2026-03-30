import tkinter as tk
from tkinter import messagebox


def form():
    name = nome.get()
    mail = email.get()
    messagebox.showinfo("Informação de Contato",
                        message=f"Nome: {name}\nE-mail: {mail}")


window = tk.Tk()
window.title("Formulário de Contato")
window.geometry("300x200")
texto = tk.Label(window, text="Nome")
texto.pack(pady="5")
nome = tk.Entry(window)
nome.pack(pady="5")
texto2 = tk.Label(window, text="E-mail")
texto2.pack(pady="5")
email = tk.Entry(window)
email.pack(pady="5")
click = tk.Button(window, text="Enviar", command=(form))
click.pack(pady="15")

window.mainloop()
