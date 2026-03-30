import datetime as dt


class Empresa:
    def __init__(self, nome, localizacao, data_criacao, numero_funcionarios):
        self.nome = nome
        self.localizacao = localizacao
        self.data_criacao = data_criacao
        self.numero_funcionarios = numero_funcionarios
        self.lista_departamentos = []

    def calcular_idade(self):
        idade = dt.datetime.today().year - self.data_criacao.year
        if (dt.datetime.today().month, dt.datetime.today().day) > (self.data_criacao.month, self.data_criacao.day):
            idade -= 1
        return idade

    def classificar_dimensao(self):
        if self.numero_funcionarios < 10:
            return "Microempresa"
        elif self.numero_funcionarios < 50:
            return "Pequena Empresa"
        elif self.numero_funcionarios < 250:
            return "Média Empresa"
        else:
            return "Grande Empresa"
