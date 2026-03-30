import datetime as dt


class Funcionario:
    def __init__(self, nome, morada, telefone, data_nascimento, salario_base):
        self.nome = nome
        self.morada = morada
        self.telefone = telefone
        self.data_nascimento = dt.datetime.strptime(
            data_nascimento, "%d/%m/%Y")
        self.salario_base = salario_base

    def calcular_idade(self):
        idade = dt.datetime.today().date().year - self.data_nascimento.year
        if self.data_nascimento.month > dt.datetime.today().date().month:
            idade -= 1
        elif self.data_nascimento.month == self.data_nascimento.month > dt.datetime.today().date().month and self.data_nascimento.day > dt.datetime.today().date().day:
            idade -= 1
        return idade

    def calcular_salario_liquido(self):
        return self.salario_base - (self.salario_base * 0.41)

    def comparar_salario_base(self, funcionario):
        if funcionario.salario_base > self.salario_base:
            return f"O funcionário {funcionario.nome} ganha mais que tu!"
        elif funcionario.salario_base < self.salario_base:
            return f"O funcionário {funcionario.nome} ganha menos que tu!"
        else:
            return f"O funcionário {funcionario.nome} ganha o mesmo que tu!"
