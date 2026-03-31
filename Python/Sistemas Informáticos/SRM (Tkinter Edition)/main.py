from classes import SistemaCRM, Encomenda, Item, Fornecedor, Produto
import datetime as dt
import tkinter as tk
from tkinter import messagebox as mbx
from tkinter import ttk
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


def criar_produto():
    criar_prod_window = tk.Toplevel(window)
    criar_prod_window.geometry("500x500")
    # CÓDIGO DO PRODUTO
    tk.Label(criar_prod_window, text="Código",
             font=("Comic Sans MS", 20)).pack(pady=5)
    codigo_entry = tk.Entry(criar_prod_window)
    codigo_entry.pack()
    # NOME DO PRODUTO
    tk.Label(criar_prod_window, text="Nome",
             font=("Comic Sans MS", 20)).pack(pady=5)
    nome_entry = tk.Entry(criar_prod_window)
    nome_entry.pack()
    # CATEGORIA DO PRODUTO
    tk.Label(criar_prod_window, text="Categoria",
             font=("Comic Sans MS", 20)).pack(pady=5)
    categoria_entry = tk.Entry(criar_prod_window)
    categoria_entry.pack()
    # PREÇO DO PRODUTO
    tk.Label(criar_prod_window, text="Preço",
             font=("Comic Sans MS", 20)).pack(pady=5)
    preco_entry = tk.Entry(criar_prod_window)
    preco_entry.pack()
    tk.Button(criar_prod_window, text="Criar",
              command=lambda: verificar_adicionar_produto(criar_prod_window, codigo_entry, nome_entry, categoria_entry, preco_entry)).pack(pady=5)


def criar_encomenda():
    criar_enco_window = tk.Toplevel(window)
    criar_enco_window.geometry("500x500")
    # NÚMERO DA ENCOMENDA
    tk.Label(criar_enco_window, text="Número",
             font=("Comic Sans MS", 20)).pack(pady=5)
    codigo_entry = tk.Entry(criar_enco_window)
    codigo_entry.pack()
    # DATA DA ENCOMENDA
    tk.Label(criar_enco_window, text="Data (Dia/Mês/Ano)",
             font=("Comic Sans MS", 20)).pack(pady=5)
    data_entry = tk.Entry(criar_enco_window)
    data_entry.pack()
    # FORNECEDOR DA ENCOMENDA
    # THE REAL DEAL!!! (Again...)
    tk.Label(criar_enco_window, text="Fornecedor",
             font=("Comic Sans MS", 20)).pack(pady=5)
    fornecedor_entry = ttk.Combobox(
        criar_enco_window, values=backend_system.lista_fornecedores)
    fornecedor_entry.pack()
    # THE REAL DEAL!!!
    tk.Label(criar_enco_window, text="Produtos",
             font=("Comic Sans MS", 20)).pack(pady=5)
    produtos_entry = tk.Listbox(
        criar_enco_window, values=backend_system.lista_produtos)
    produtos_entry.pack()
    tk.Button(criar_enco_window, text="Criar",
              command=lambda: verificar_adicionar_produto(criar_enco_window, codigo_entry, data_entry, fornecedor_entry, produtos_entry)).pack(pady=5)


def verificar_adicionar_produto(prod_window, codigo_entry, data_entry, fornecedor_entry, produtos_entry):
    pass  # Will do at home, so in a bit XD


def verificar_adicionar_produto(prod_window, codigo_entry, nome_entry, categoria_entry, preco_entry):
    code = str(codigo_entry.get())
    name = str(nome_entry.get())
    category = str(categoria_entry.get())
    if code == "":
        mbx.showerror("ERRO!", "O código está vazio!")
    elif name == "":
        mbx.showerror("ERRO!", "O nome está vazio!")
    elif category == "":
        mbx.showerror("ERRO!", "A categoria está vazio!")
    else:
        try:
            price = float(preco_entry.get())
        except ValueError:
            mbx.showerror(
                "ERRO!", "O preço apenas pode conter números!")
        else:

            if price <= 0:
                mbx.showerror(
                    "ERRO!", "O preço tem de ser maior que 0!")
            else:
                backend_system.adicionar_produto(
                    Produto(code, name, category, price))
                prod_window.destroy()
                mbx.showinfo("Produto criado!",
                             f"O produto {name} foi criado!")


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
            forn_lista.delete(0, "end")
            for forn in backend_system.lista_fornecedores:
                forn_lista.insert(
                    contar, f"{forn.codigo} | {forn.nome} | {forn.contacto} | {forn.email} | {forn.avaliacao_qualidade} | {forn.avaliacao_cumprimento_prazos} | {forn.avaliacao_total()}")
                contar += 1
        forn_window = tk.Toplevel(window)
        forn_window.geometry("500x350")
        tk.Label(forn_window, text="Fornecedores",
                 font=("Comic Sans MS", 20)).pack(pady=20)
        forn_lista = tk.Listbox(forn_window, width=60,
                                justify="center", font=("Comic Sans MS", 10))
        refresh(forn_lista)
        forn_lista.pack()
        tk.Button(forn_window, text="Criar Fornecedor",
                  command=criar_fornecedor).pack(pady=5)
        tk.Button(forn_window, text="Reiniciar Listagem",
                  command=lambda: refresh(forn_lista)).pack(pady=5)


def on_click_produtos():
    if len(backend_system.lista_produtos) <= 0:
        primeira_vez_prod = mbx.askyesno("Sem produto adicionado!",
                                         "Aviso! Você ainda não adicionou nenhum produto!\nGostaria de adicionar um?")
        if primeira_vez_prod == True:
            criar_produto()
    else:
        def refresh(prod_lista):
            contar = 0
            prod_lista.delete(0, "end")
            for prod in backend_system.lista_produtos:
                prod_lista.insert(
                    contar, f"{prod.codigo} | {prod.nome} | {prod.categoria} | {prod.preco}€")
                contar += 1
        prod_window = tk.Toplevel(window)
        prod_window.geometry("500x350")
        tk.Label(prod_window, text="Produtos",
                 font=("Comic Sans MS", 20)).pack(pady=20)
        prod_lista = tk.Listbox(prod_window, width=60,
                                justify="center", font=("Comic Sans MS", 10))
        refresh(prod_lista)
        prod_lista.pack()
        tk.Button(prod_window, text="Criar Produto",
                  command=criar_produto).pack(pady=5)
        tk.Button(prod_window, text="Reiniciar Listagem",
                  command=lambda: refresh(prod_lista)).pack(pady=5)


def on_click_encomendas():
    if len(backend_system.lista_encomendas) <= 0:
        primeira_vez_enco = mbx.askyesno("Sem encomenda adicionado!",
                                         "Aviso! Você ainda não adicionou nenhuma encomenda!\nGostaria de adicionar uma?")
        if primeira_vez_enco == True:
            criar_encomenda()
    else:
        def refresh(enco_lista):
            contar = 0
            enco_lista.delete(0, "end")
            for enco in backend_system.lista_encomendas:
                enco_lista.insert(
                    contar, f"{enco.codigo} | {enco.nome} | {enco.categoria} | {enco.preco}€")
                contar += 1
        enco_window = tk.Toplevel(window)
        enco_window.geometry("500x350")
        tk.Label(enco_window, text="Encomendas",
                 font=("Comic Sans MS", 20)).pack(pady=20)
        enco_lista = tk.Listbox(enco_window, width=60,
                                justify="center", font=("Comic Sans MS", 10))
        refresh(enco_lista)
        enco_lista.pack()
        tk.Button(enco_window, text="Criar Produto",
                  command=criar_produto).pack(pady=5)
        tk.Button(enco_window, text="Reiniciar Listagem",
                  command=lambda: refresh(enco_lista)).pack(pady=5)


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
