import random as rd


class Elevador:
    def __init__(self):
        self.peso_maximo = 0
        self.andar_atual = 0
        self.lista_passageiros = []

    def calcular_peso(self):
        self.peso_maximo = round(rd.uniform(100, 300), 2)

    def mostrar_andar(self):
        return self.andar_atual

    def retorna_passageiros(self, lista):
        if lista == False:
            print(f"Passageiros:\n")
            for pessoa in self.lista_passageiros:
                print(f"Nome: {pessoa.nome}")
                print(f"Ano de Nascimento: {pessoa.ano_nascimento}\n", "-"*10)
        else:
            for pessoa in self.lista_passageiros:
                print(pessoa.nome)

    def mudar_andar(self, novo_andar):
        self.andar_atual = novo_andar

    def adicionar_passageiro(self, pessoa):
        self.lista_passageiros.append(pessoa)

    def remover_passageiro(self, passageiro):
        self.lista_passageiros.remove(self.lista_passageiros[passageiro])

    def remover_todos(self):
        self.lista_passageiros = []
