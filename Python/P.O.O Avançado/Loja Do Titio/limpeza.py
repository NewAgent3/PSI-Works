from funcionario import Funcionario
import datetime as dt


class Limpeza(Funcionario):
    def __init__(self, nome, morada, telefone, data_nascimento, salario_base, n_horas_extra):
        super().__init__(nome, morada, telefone, data_nascimento, salario_base)
        self.horas_extra = n_horas_extra

    def calcular_salario_liquido(self):
        return super().calcular_salario_liquido() + (self.horas_extra * 5)
