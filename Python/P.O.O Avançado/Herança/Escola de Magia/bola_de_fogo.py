from truque_elemento import TruqueElemento


class BolaDeFogo(TruqueElemento):
    def __init__(self, nivel):
        self.nivel = nivel
        self.nome = "Bola de Fogo"
        self.elemento = "Fogo"

    def usar(self):
        print("Lançaste uma enorme bola de fogo!")
