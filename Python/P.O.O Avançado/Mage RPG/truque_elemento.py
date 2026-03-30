from truque import Truque


class TruqueElemento(Truque):
    def __init__(self, nome, nivel, elemento):
        super().__init__(nome, nivel)
        self.elemento = elemento

    def info(self):
        print(
            f"Nome: {self.nome} | Nível: {self.nivel} | Elemento: {self.elemento}")
