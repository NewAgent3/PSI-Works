from pessoa import Pessoa


class Aluno(Pessoa):
    def __init__(self, nome, data_nascimento, altura, n_processo, curso):
        super().__init__(nome, data_nascimento, altura)
        self.n_processo = n_processo
        self.curso = curso
        self.notas = []

    def calcular_media(self):
        return sum(self.notas) / len(self.notas)

    def adicionar_notas(self, nota):
        self.notas.append(nota)

    def estado(self):
        if self.calcular_media() >= 10:
            return "Aprovado!"
        else:
            return "Reprovado!"
