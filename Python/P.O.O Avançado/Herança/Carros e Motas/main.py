from mota import Mota
from carro import Carro
import os
while True:
    try:
        os.system("cls")
        carro_teste = Carro("Honda", "CRX", "5")
        print(carro_teste.descricao())
        mota_teste = Mota("Yamaha", "R1", 1000)
        print(mota_teste.descricao(), "\n")
        escolha = int(input("1 - Carro\n2 - Mota\n\nInput: "))
        match escolha:
            case 1:
                marca = input("\nMarca: ")
                modelo = input("Modelo: ")
                n_portas = int(input("Nº Portas: "))
                while True:
                    if n_portas <= 0:
                        n_portas = int(input("Nº Portas inválido: "))
                    else:
                        break
                carro = Carro(marca, modelo, n_portas)
                print(carro.descricao())
                break
            case 2:
                marca = input("\nMarca: ")
                modelo = input("Modelo: ")
                cilindrada = int(input("Cilindrada: "))
                while True:
                    if cilindrada <= 0:
                        cilindrada = int(input("Cilindrada inválida: "))
                    else:
                        break
                mota = Mota(marca, modelo, cilindrada)
                print(mota.descricao())
                break
            case _:
                print("\nNão tem outra opção XD\n")
    except BaseException:
        os.system("cls")
        pass
