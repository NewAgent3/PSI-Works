import random as rnd
import os


class Bicicleta:
    def __init__(self):
        self.numref = rnd.randint(1, 99999)
        self.numkm = 0
        self.local = "Estação"

    def obterattr(self):
        print(
            f"Nº referência: {self.numref}\nNº quilómetros: {self.numkm}\nLocal: {self.local}")

    def addkm(self, km):
        self.numkm += km

    def viagem(self, destino, km):
        self.local = destino
        self.numkm += km

    def reiniciar(self):
        self.numkm = 0
        self.local = "Estação"


bicicleta1 = Bicicleta()
while True:
    os.system("cls")
    print("=== Menu ===")
    print("1 - Ver informação")
    print("2 - Adicionar quilómetros")
    print("3 - Fazer viagem")
    print("4 - Reiniciar rota")
    print("0 - Sair")
    try:
        opcao = int(input(("\nOpção: ")))
        match opcao:
            case 1:
                bicicleta1.obterattr()
                input("\nPressione Enter para voltar...")
            case 2:
                km = int(input("Nº quilómetros: "))
                while True:
                    if km <= 0:
                        km = int(input("Nº quilómetros inválido: "))
                    else:
                        break
                bicicleta1.addkm(km)
                input("\nPressione Enter para voltar...")
            case 3:
                destino = input("Destino: ")
                km = int(input("Nº quilómetros: "))
                while True:
                    if km <= 0:
                        km = int(input("Nº quilómetros inválido: "))
                    else:
                        break
                bicicleta1.viagem(destino, km)
                input("\nPressione Enter para voltar...")
            case 4:
                bicicleta1.reiniciar()
                input("\nPressione Enter para voltar...")
            case 0:
                os.system("cls")
                quit()
            case _:
                pass
    except ValueError:
        pass
