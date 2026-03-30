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


def criar_adicionar_fornecedor(code, name, phone, email, rating_quality, rating_deadlines):
    backend_system.adicionar_fornecedor(Fornecedor(
        code, name, phone, email, rating_quality, rating_deadlines))


def on_click_fornecedores():
    if len(backend_system.lista_fornecedores) <= 0:
        primeira_vez_forn = mbx.askyesno("Sem fornecedor adicionado!",
                                         "Aviso! Você ainda não adicionou nenhum fornecedor!\nGostaria de adicionar um?")
        if primeira_vez_forn == True:
            criar_forn_window = tk.Toplevel(window)
            criar_forn_window.geometry("500x500")
            # CÓDIGO DO FORNECEDOR
            tk.Label(criar_forn_window, text="Código",
                     font=("Comic Sans MS", 20)).pack(pady=5)
            codigo = tk.Entry(criar_forn_window).pack()
            # NOME DO FORNECEDOR
            tk.Label(criar_forn_window, text="Nome",
                     font=("Comic Sans MS", 20)).pack(pady=5)
            nome = tk.Entry(criar_forn_window).pack()
            # CONTACTO DO FORNECEDOR
            tk.Label(criar_forn_window, text="Contacto",
                     font=("Comic Sans MS", 20)).pack(pady=5)
            contacto = tk.Entry(criar_forn_window).pack()
            # E-MAIL DO FORNECEDOR
            tk.Label(criar_forn_window, text="E-Mail",
                     font=("Comic Sans MS", 20)).pack(pady=5)
            email = tk.Entry(criar_forn_window).pack()
            # AVALIAÇÃO DA QUALIDADE DO FORNECEDOR
            tk.Label(criar_forn_window, text="Avaliação (Qualidade)",
                     font=("Comic Sans MS", 20)).pack(pady=5)
            avaliacao_qualidade = tk.Entry(criar_forn_window).pack()
            # AVALIAÇÃO DO CUMPRIMENTO DE PRAZOS DO FORNECEDOR
            tk.Label(criar_forn_window, text="Avaliação (Cumprimento de Prazos)",
                     font=("Comic Sans MS", 20)).pack(pady=5)
            avaliacao_cumprimento_prazos = tk.Entry(criar_forn_window).pack()
            tk.Button(criar_forn_window, text="Criar",
                      command=criar_adicionar_fornecedor(codigo, nome, contacto, email, avaliacao_qualidade, avaliacao_cumprimento_prazos)).pack(pady=5)
    else:
        forn_window = tk.Toplevel(window)
        forn_window.geometry("300x280")
        tk.Label(forn_window, text="Fornecedores",
                 font=("Comic Sans MS", 20)).pack(pady=20)


def on_click_produtos():
    prod_window = tk.Toplevel(window)
    prod_window.geometry("300x280")
    tk.Label(prod_window, text="Produtos",
             font=("Comic Sans MS", 20)).pack(pady=20)


def on_click_encomendas():
    enco_window = tk.Toplevel(window)
    enco_window.geometry("300x280")
    tk.Label(enco_window, text="Encomendas",
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
tk.Label(window, text="SRM SYSTEM (PRO)",
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
