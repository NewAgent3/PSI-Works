import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage


def cf():
    cel = celsius.get()
    if cel == '':
        messagebox.showerror(
            "ERRO", message="Tem de introduzir um valor no campo Celsius!")
    else:
        cel = float(cel)
        fah = cel * (9/5) + 32
        fah = round(fah, 1)
        messagebox.showinfo("Celsius Para Fahrenheit",
                            message=f"{cel}℃ é igual a {fah}℉")


def fc():
    fah = fahrenheit.get()
    if fah == '':
        messagebox.showerror(
            "ERRO", message="Tem de introduzir um valor no campo Fahrenheit!")
    else:
        fah = float(fah)
        cel = (fah - 32) * (5/9)
        cel = round(cel, 1)
        messagebox.showinfo("Fahrenheit Para Celsius",
                            message=f"{fah}℉ é igual a {cel}℃")


window = tk.Tk()
window.title("Convertor de Temperatura | Afonso Almeida 11ºK")
window.geometry("450x400")
window.resizable(False, False)
back = PhotoImage(file="fundo.png")
ground = tk.Label(window, image=back)
ground.place(x=-5, y=0)
celsiusL = tk.Label(window, text="Celsius:", bg="#546bab",
                    fg="#ffffff", font=("", 20))
celsiusL.pack(pady="5")
celsius = tk.Entry(window, bg="#546bab", fg="#ffffff", font=("", 20))
celsius.pack(pady="5")
fahrenheitL = tk.Label(window, text="Fahrenheit:",
                       bg="#546bab", fg="#ffffff", font=("", 20))
fahrenheitL.pack(pady="5")
fahrenheit = tk.Entry(window, bg="#546bab", fg="#ffffff", font=("", 20))
fahrenheit.pack(pady="5")
titulo = tk.Label(window, text="Escolha uma das opções:",
                  bg="#546bab", fg="#ffffff", font=("", 20))
titulo.pack(pady="25")
op1 = tk.Button(window, text="Celsius Para Fahrenheit",
                command=(cf), bg="#546bab", fg="#ffffff", font=("", 20))
op1.pack(pady="0")
op2 = tk.Button(window, text="Fahrenheit Para Celsius",
                command=(fc), bg="#546bab", fg="#ffffff", font=("", 20))
op2.pack(pady="10")
window.mainloop()
