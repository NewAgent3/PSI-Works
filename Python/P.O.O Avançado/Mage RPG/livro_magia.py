class LivroDeMagia:
    def __init__(self):
        self.truques = []

    def adicionar(self, novo_truque):
        self.truques.append(novo_truque)

    def listar(self):
        for truque in self.truques:
            truque.info()

    def usar_todos(self):
        for truque in self.truques:
            truque.usar()
