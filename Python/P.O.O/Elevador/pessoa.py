class Pessoa:
    def __init__(self, nome, ano_nascimento):
        self.nome = nome
        self.ano_nascimento = ano_nascimento

    def alterar_nome(self, novo_nome):
        self.nome = novo_nome

    def calcular_idade(self):
        return 2025 - self.ano_nascimento
