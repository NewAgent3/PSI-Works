class Curso:
    def __init__(self, nome):
        self.nome = nome
        self.disciplinas = []

    def adiconar_disciplina(self, disciplina):
        self.disciplinas.append(disciplina)

    def remover_disciplina(self, disciplina):
        self.disciplinas.remove(disciplina)

    def remover_todas_disciplinas(self):
        self.disciplinas = []
