nomes = ("Ana", "Bruno", "Carla", "Dinis", "Eva")
try:
    num = int(input("Posição do nome na lista: "))
except ValueError:
    print("ValueError! Não é um número inteiro!")
else:
    try:
        print(nomes[num - 1])
    except IndexError:
        print("IndexError! Número escolhido não é uma posição válida na lista!")
finally:
    print("Operação terminada")
    quit()
