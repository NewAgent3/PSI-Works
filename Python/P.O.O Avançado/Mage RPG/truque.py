class Truque:
    def __init__(self, nome, nivel):
        self.nome = nome
        self.nivel = nivel

    def usar(self):
        print("Usou um truque!")

    def info(self):
        print(f"Nome: {self.nome} | Nível: {self.nivel}")
