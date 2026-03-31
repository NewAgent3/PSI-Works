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


def criar_fornecedor():
    criar_forn_window = tk.Toplevel(window)
    criar_forn_window.geometry("500x500")
    # CÓDIGO DO FORNECEDOR
    tk.Label(criar_forn_window, text="Código",
             font=("Comic Sans MS", 20)).pack(pady=5)
    codigo_entry = tk.Entry(criar_forn_window)
    codigo_entry.pack()
    # NOME DO FORNECEDOR
    tk.Label(criar_forn_window, text="Nome",
             font=("Comic Sans MS", 20)).pack(pady=5)
    nome_entry = tk.Entry(criar_forn_window)
    nome_entry.pack()
    # CONTACTO DO FORNECEDOR
    tk.Label(criar_forn_window, text="Contacto",
             font=("Comic Sans MS", 20)).pack(pady=5)
    contacto_entry = tk.Entry(criar_forn_window)
    contacto_entry.pack()
    # E-MAIL DO FORNECEDOR
    tk.Label(criar_forn_window, text="E-Mail",
             font=("Comic Sans MS", 20)).pack(pady=5)
    email_entry = tk.Entry(criar_forn_window)
    email_entry.pack()
    # AVALIAÇÃO DA QUALIDADE DO FORNECEDOR
    tk.Label(criar_forn_window, text="Avaliação (Qualidade)",
             font=("Comic Sans MS", 20)).pack(pady=5)
    avaliacao_qualidade_entry = tk.Entry(criar_forn_window)
    avaliacao_qualidade_entry.pack()
    # AVALIAÇÃO DO CUMPRIMENTO DE PRAZOS DO FORNECEDOR
    tk.Label(criar_forn_window, text="Avaliação (Cumprimento de Prazos)",
             font=("Comic Sans MS", 20)).pack(pady=5)
    avaliacao_cumprimento_prazos_entry = tk.Entry(
        criar_forn_window)
    avaliacao_cumprimento_prazos_entry.pack()
    tk.Button(criar_forn_window, text="Criar",
              command=lambda: verificar_adicionar_fornecedor(criar_forn_window, codigo_entry, nome_entry, contacto_entry, email_entry, avaliacao_qualidade_entry, avaliacao_cumprimento_prazos_entry)).pack(pady=5)


def verificar_adicionar_fornecedor(forn_window, codigo_entry, nome_entry, contacto_entry, email_entry, avaliacao_qualidade_entry, avaliacao_cumprimento_prazos_entry):
    code = str(codigo_entry.get())
    name = str(nome_entry.get())
    phone = str(contacto_entry.get())
    email = str(email_entry.get())
    rating_quality = avaliacao_qualidade_entry.get()
    rating_deadlines = avaliacao_cumprimento_prazos_entry.get()
    if code == "":
        mbx.showerror("ERRO!", "O código está vazio!")
    elif name == "":
        mbx.showerror("ERRO!", "O nome está vazio!")
    elif phone == "":
        mbx.showerror("ERRO!", "O contacto está vazio!")
    elif email == "":
        mbx.showerror("ERRO!", "O e-mail está vazio!")
    elif rating_quality == "":
        mbx.showerror(
            "ERRO!", "A avaliação da qualidade está vazia!")
    elif rating_deadlines == "":
        mbx.showerror(
            "ERRO!", "A avaliação de cumprimento de prazos está vazia!")
    else:
        try:
            rating_quality = int(rating_quality)
            rating_deadlines = int(rating_deadlines)
        except ValueError:
            mbx.showerror(
                "ERRO!", "Uma das avaliações contêm letras!")
        else:

            if (rating_deadlines <= 0 or rating_quality <= 0) or (rating_deadlines >= 100 or rating_quality >= 100):
                mbx.showerror(
                    "ERRO!", "A avaliação da qualidade e/ou do cumprimento de prazos está abaixo de 0 ou acima de 100!")
            else:
                backend_system.adicionar_fornecedor(Fornecedor(
                    code, name, phone, email, rating_quality, rating_deadlines, []))
                forn_window.destroy()
                mbx.showinfo("Fornecedor criado!",
                             f"O fornecedor {name} foi criado!")


def on_click_fornecedores():
    if len(backend_system.lista_fornecedores) <= 0:
        primeira_vez_forn = mbx.askyesno("Sem fornecedor adicionado!",
                                         "Aviso! Você ainda não adicionou nenhum fornecedor!\nGostaria de adicionar um?")
        if primeira_vez_forn == True:
            criar_fornecedor()
    else:
        def refresh(forn_lista):
            contar = 0
            for forn in backend_system.lista_fornecedores:
                forn_lista.insert(
                    contar, f"{forn.codigo} | {forn.nome} | {forn.avaliacao_total()}")
                contar += 1
        forn_window = tk.Toplevel(window)
        forn_window.geometry("500x280")
        tk.Label(forn_window, text="Fornecedores",
                 font=("Comic Sans MS", 20)).pack(pady=20)
        forn_lista = tk.Listbox(forn_window, width=50, justify="center")
        refresh(forn_lista)
        forn_lista.pack()
        tk.Button(forn_window, text="Criar Fornecedor",
                  command=criar_fornecedor).pack(pady=5)
        tk.Button(forn_window, text="Reiniciar Listagem",
                  command=refresh).pack(pady=5)


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
