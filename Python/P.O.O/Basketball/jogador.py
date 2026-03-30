class Jogador:
    def __init__(self, num, nome, ano_nascimento, posicao):
        self.numero = num
        self.nome = nome
        self.ano_nascimento = ano_nascimento
        self.posicao = posicao

    def alterar_posicao(self, nova_posicao):
        self.posicao = nova_posicao

    def alterar_numero(self, novo_numero):
        self.numero = novo_numero

    def devolver_idade(self):
        return 2025 - self.ano_nascimento

    def __str__(self):
        return f"Nome: {self.nome}\nNúmero: {self.numero}\nAno Nascimento: {self.ano_nascimento}\nPosição: {self.posicao}"
