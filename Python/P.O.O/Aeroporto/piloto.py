class Piloto:
    def __init__(self, nome, brevet, ano_nascimento):
        self.nome = nome
        self.brevet = brevet
        self.ano_nascimento = ano_nascimento

    def mostrar_nome(self):
        return self.nome

    def calcular_idade(self, data_tempo):
        return data_tempo.year() - self.ano_nascimento

    def __str__(self):
        return f"{self.nome}\n{self.brevet}\n{self.ano_nascimento}"
