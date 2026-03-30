class Equipa:
    def __init__(self, nome, jogadores):
        self.nome = nome
        self.jogadores = jogadores

    def adicionar_jogadores(self, jog):
        self.jogadores.append(jog)

    def mostrar_nome(self):
        return self.nome

    def mostrar_info(self):
        info = f"Nome da equipa: {self.nome}\nJogadores:\n"
        for jogador in self.jogadores:
            info += f"  - {jogador.nome} ({jogador.numero}, {jogador.posicao})\n"
        return info
