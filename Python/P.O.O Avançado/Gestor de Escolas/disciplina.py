class Disciplina:
    def __init__(self, nome, dia_semana_dado, carga_anual):
        self.nome = nome
        self.dia_semana_dado = dia_semana_dado
        self.carga_anual = carga_anual

    def alterar_horario(self, novo_horario):
        self.dia_semana_dado = novo_horario
