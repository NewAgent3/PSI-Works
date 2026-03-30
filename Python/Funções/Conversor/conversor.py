def c_para_f(celsius):
    return (celsius * 1.8) + 32


def f_para_c(fahrenheit):
    return (fahrenheit - 32) / 1.8


def menu():
    print("Como usar:\n1 - Introduza os valores\n2 - Selecionar a opção desejada\n")
    print("Opções:\n1 - Celsius para Fahrenheit\n2 - Fahrenheit para Celsius\n3 - Sair\n")
