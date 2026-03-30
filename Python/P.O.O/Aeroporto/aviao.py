class Aviao:
    def __init__(self, matricula, nome, n_lugares, autonomia):
        self.matricula = matricula
        self.nome = nome
        self.n_lugares = n_lugares
        self.autonomia = autonomia

    def mostrar_autonomia(self):
        return self.autonomia

    def mudar_nome(self, novo_nome):
        self.nome = novo_nome

    def mudar_lugares(self, lugares):
        self.n_lugares = lugares

    def __str__(self):
        return f"{self.matricula}\n{self.nome}\n{self.n_lugares}\n{self.autonomia}"
