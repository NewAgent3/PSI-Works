import conversor as conv
import os
invalido = 0
while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    conv.menu()
    if invalido == 1:
        opcao = int(input("Opção inválida: "))
        invalido = 0
    else:
        opcao = int(input("Opção: "))
    match(opcao):
        case 1:
            celsius = float(input("Celsius: "))
            print(f"{conv.c_para_f(celsius)}°F")
            input("\nFeito! Pressione qualquer tecla para voltar...")
        case 2:
            fahrenheit = float(input("Fahrenheit: "))
            print(f"{conv.f_para_c(fahrenheit)}°C")
            input("\nFeito! Pressione qualquer tecla para voltar...")
        case 3:
            quit()
        case _:
            invalido = 1
            pass
