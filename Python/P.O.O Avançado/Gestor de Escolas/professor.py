from pessoa import Pessoa


class Professor(Pessoa):
    def __init__(self, nome, data_nascimento, altura, salario_bruto, disciplina):
        super().__init__(nome, data_nascimento, altura)
        self.salario_bruto = salario_bruto
        self.disciplina = disciplina

    def calcular_salario_liquido(self):
        return self.salario_bruto * 0.60

    def calcular_tempo_lecionar(self, aulas_por_semana):
        return self.disciplina.carga_anual / aulas_por_semana
