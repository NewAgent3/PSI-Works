from classes import SistemaCRM, Encomenda, Item, Fornecedor, Produto
import datetime as dt
import tkinter as tk
from tkinter import messagebox as mbx
from PIL import Image, ImageTk
import os
import playsound3 as ps3
import threading as thd

backend_system = SistemaCRM()


def startup():
    ps3.playsound("SFX/startup.mp3")  # Windows XP lookin' ahh XD


def on_click_fornecedores():
    if len(backend_system.lista_fornecedores) <= 0:
        mbx.showwarning("Sem fornecedor adicionado!",
                        "Aviso! Você ainda não adicionou nenhum fornecedor!\nGostaria de adicionar um?")
    else:
        forn_window = tk.Toplevel(window)
        forn_window.geometry("300x280")
        title_forn = tk.Label(forn_window, text="Fornecedores",
                              font=("Comic Sans MS", 20)).pack(pady=20)


def on_click_produtos():
    prod_window = tk.Toplevel(window)
    prod_window.geometry("300x280")
    title_forn = tk.Label(prod_window, text="Produtos",
                          font=("Comic Sans MS", 20)).pack(pady=20)


def on_click_encomendas():
    enco_window = tk.Toplevel(window)
    enco_window.geometry("300x280")
    title_forn = tk.Label(enco_window, text="Encomendas",
                          font=("Comic Sans MS", 20)).pack(pady=20)


os.system("cls")  # Limpa o terminal para debugging
# Janela principal!
window = tk.Tk()
window.title("SRM System (PRO)")  # Não existe versão free XD
window.geometry("300x280")
window.resizable(False, False)
bg_image = Image.open("images/bg_image.jpg")  # PORCARIA
bg_image = bg_image.resize((300, 280), Image.LANCZOS)  # DO
bg_image = ImageTk.PhotoImage(bg_image)  # TKINTER
bg_label = tk.Label(window, image=bg_image).place(
    x=0, y=0, relwidth=1, relheight=1)  # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
title = tk.Label(window, text="SRM SYSTEM (PRO)",
                 font=("Comic Sans MS", 20)).pack(pady=20)
# The greatest font that there ever will exist XD
btn_fornecedores = tk.Button(
    window, text="Fornecedores", font=("Comic Sans MS", 16), command=on_click_fornecedores).pack(pady=5)
btn_produtos = tk.Button(window, text="Produtos",
                         font=("Comic Sans MS", 16), command=on_click_produtos).pack(pady=5)
btn_encomendas = tk.Button(window, text="Encomendas",
                           font=("Comic Sans MS", 16), command=on_click_encomendas).pack(pady=5)
thd.Thread(target=startup, daemon=True).start()
window.mainloop()  # You spin me round baby, right round!
ps3.playsound("SFX/shutdown.mp3")  # Windows XP lookin' ahh XD
