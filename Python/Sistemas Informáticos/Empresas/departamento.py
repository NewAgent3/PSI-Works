class Departamento:
    def __init__(self, nome, orcamento):
        self.nome = nome
        self.orcamento = orcamento

    def alterar_orcamento(self, valor):
        self.orcamento = valor
