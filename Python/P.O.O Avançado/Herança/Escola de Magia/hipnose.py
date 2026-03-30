from truque_mental import TruqueMental


class Hipnose(TruqueMental):
    def __init__(self, nivel, dificuldade):
        self.nivel = nivel
        self.dificuldade = dificuldade
        self.nome = "Hipnose"

    def usar(self):
        print("Tentaste hipnotizar o alvo...")
