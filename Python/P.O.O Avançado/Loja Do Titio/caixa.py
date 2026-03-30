from funcionario import Funcionario
import datetime as dt


class Caixa(Funcionario):
    def __init__(self, nome, morada, telefone, data_nascimento, salario_base):
        super().__init__(nome, morada, telefone, data_nascimento, salario_base)
        self.subsidio_risco = 50

    def calcular_salario_liquido(self):
        return super().calcular_salario_liquido() + self.subsidio_risco
