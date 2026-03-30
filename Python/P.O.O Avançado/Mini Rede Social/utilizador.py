class Utilizador:
    def __init__(self, nome):
        self.nome = nome

    def __str__(self):
        return f"Utilizador: {self.nome}"
