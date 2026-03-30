class Comentario:
    def __init__(self, utilizador, texto):
        self.autor = utilizador
        self.texto = texto

    def __str__(self):
        return f"{self.autor}: {self.texto}"
