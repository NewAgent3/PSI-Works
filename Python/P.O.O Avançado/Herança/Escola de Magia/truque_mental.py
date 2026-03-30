from truque import Truque


class TruqueMental(Truque):
    def __init__(self, nome, nivel, dificuldade):
        super().__init__(nome, nivel)
        self.dificuldade = dificuldade

    def info(self):
        print(
            f"Nome: {self.nome} | Nível: {self.nivel} | Dificuldade: {self.dificuldade}")
