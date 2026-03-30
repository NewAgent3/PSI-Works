import random as rd


class Iphone:
    def __init__(self, num_serie, modelo):
        self.num_serie = num_serie
        self.modelo = modelo
        self.cor = None
        self.preso = None
        self.estado_ligado = False
        self.estado = "Não Testado"

    def testa_unidade(self):
        estado = rd.randint(0, 100)
        if estado >= 50:
            self.estado = "Aprovado"
            return True
        else:
            self.estado = "Não Aprovado"
            return False

    def alterar_peso(self, peso):
        self.preso = peso

    def ligar(self):
        self.estado_ligado = True

    def desligar(self):
        self.estado_ligado = False

    def mudar_cor(self, cor):
        self.cor = cor

    def __str__(self):
        return f"Nº Série: {self.num_serie}\nModelo: {self.modelo}\nCor: {self.cor}\nPeso: {self.preso}g\nLigado: {self.estado_ligado}\nEstado: {self.estado}"
