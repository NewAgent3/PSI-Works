class Cartao:
    def __init__(self, nome, ano_turma):
        self.aluno = nome
        self.ano_turma = ano_turma
        self.ativacao = True
        self.entrada = True
        self.saldo = 0

    def ativar_cartao(self):
        self.ativacao = True

    def entrada_escola(self):
        self.entrada = True

    def saida_escola(self):
        self.entrada = False

    def carregar_cartao(self, dinheiro):
        self.saldo += dinheiro

    def processar_compra(self, preco):
        if self.saldo < preco:
            return False
        else:
            self.saldo -= preco

    def anular_cartao(self):
        self.ativacao = False
