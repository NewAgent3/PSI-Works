import math
import os

lista = []


def menu(lista):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 20, "MENU", "=" * 20)
    print("\n1 - Raiz Quadrada")
    print("2 - Potência")
    print("3 - Área de um Círculo")
    print("4 - Arredondar")
    print("5 - Retirar decimais")
    print("6 - Distância entre dois pontos")
    print("7 - Aproximados")
    print("8 - Somar pares")
    print("9 - Maior e Menor")
    print("10 - Valor Absoluto e Arredondar para o mais próximo")
    print("0 - Sair")
    escolha = int(input("\nEscolha: "))
    match escolha:
        case 1:
            raiz_quadrada(lista)
        case 2:
            potencia(lista)
        case 3:
            area_circulo(lista)
        case 4:
            arredondar(lista)
        case 5:
            retirar_decimal(lista)
        case 6:
            distancia(lista)
        case 7:
            aproximados(lista)
        case 8:
            soma_pares(lista)
        case 9:
            menor_maior_lista(lista)
        case 10:
            valor_ab(lista)
        case 0:
            quit()
        case _:
            os.system('cls' if os.name == 'nt' else 'clear')
            menu(lista)


def raiz_quadrada(lista):
    num = int(input("\nDiga um número: "))
    if num < 0:
        print("Não pode ser menor que zero!")
    else:
        print(math.sqrt(num))
    input("\nPressione Enter para voltar...")
    menu(lista)


def potencia(lista):
    base = int(input("\nDiga a base: "))
    expo = int(input("Diga o expoente: "))
    print(math.pow(base, expo))
    input("\nPressione Enter para voltar...")
    menu(lista)


def area_circulo(lista):
    raio = int(input("\nDiga o raio do círculo: "))
    print(math.pi * (raio * raio))
    input("\nPressione Enter para voltar...")
    menu(lista)


def arredondar(lista):
    num = float(input("\nDiga um número com casas décimais: "))
    print(f"Arredondado para cima: {math.ceil(num)}")
    print(f"Arredondado para baixo: {math.floor(num)}")
    input("\nPressione Enter para voltar...")
    menu(lista)


def retirar_decimal(lista):
    num = float(input("\nDiga um número com casas décimais: "))
    print(math.trunc(num))
    input("\nPressione Enter para voltar...")
    menu(lista)


def distancia(lista):
    print("Primeiro Ponto: ")
    x = int(input("\nDiga o X: "))
    y = int(input("Diga o Y: "))
    ponto1 = (x, y)
    print("=" * 40, "\nSegundo Ponto: ")
    x = int(input("\nDiga o X: "))
    y = int(input("Diga o Y: "))
    ponto2 = (x, y)
    print(
        f"Distância: {math.hypot(ponto2[0] - ponto1[0], ponto2[1] - ponto1[1])}")
    input("\nPressione Enter para voltar...")
    menu(lista)


def aproximados(lista):
    num1 = float(input("\nDiga um número com casas décimais: "))
    num2 = float(input("Diga outro número com casas décimais: "))
    if math.isclose(num1, num2) == True:
        print("Os números são aproximadamente iguais!")
    else:
        print("Os números não são aproximadamente iguais!")
    input("\nPressione Enter para voltar...")
    menu(lista)


def soma_pares(lista):
    contar = 0
    while contar <= 3:
        if contar == 0:
            num = int(input("\nDiga um número: "))
            lista.append(num)
            contar += 1
        else:
            num = int(input("Diga um número: "))
            lista.append(num)
            contar += 1
        if num % 2 == 1:
            print("Tem de ser números pares!")
            contar -= 1
            lista.remove(num)
    print(sum(lista))
    input("\nPressione Enter para voltar...")
    menu(lista)


def menor_maior_lista(lista):
    if len(lista) == 0:
        print("A lista não pode estar vazia! Defina os números na opção 8!")
        input("\nPressione Enter para voltar...")
        menu(lista)
    else:
        print(f"\nMenor valor na lista: {min(lista)}")
        print(f"Maior valor na lista: {max(lista)}")
        input("\nPressione Enter para voltar...")
        menu(lista)


def valor_ab(lista):
    num = float(input("\nDiga um número com casas décimais: "))
    print(f"Valor absoluto: {math.trunc(num)}")
    if round(num % 1, 2) > .5:
        print(f"Arredondado para o mais próximo: {math.ceil(num)}")
    else:
        print(f"Arredondado para o mais próximo: {math.floor(num)}")
    input("\nPressione Enter para voltar...")
    menu(lista)


menu(lista)
