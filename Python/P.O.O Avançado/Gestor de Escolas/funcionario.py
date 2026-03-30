from pessoa import Pessoa


class Funcionario(Pessoa):
    def __init__(self, nome, data_nascimento, altura, cargo, horas_extra):
        super().__init__(nome, data_nascimento, altura)
        self.cargo = cargo
        self.horas_semanais = 35
        self.horas_extra = horas_extra

    def calcular_salario_liquido(self):
        return ((35 * 20) + (self.horas_extra * 20)) * 0.60
