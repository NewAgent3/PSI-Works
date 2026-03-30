import datetime as dt


class Pessoa:
    def __init__(self, nome, data_nascimento, altura):
        self.nome = nome
        self.data_nascimento = dt.datetime.strptime(
            data_nascimento, "%d/%m/%Y")
        self.altura = altura

    def calcular_idade(self):
        idade = dt.datetime.today().date().year - self.data_nascimento.year
        if self.data_nascimento.month > dt.datetime.today().date().month:
            idade -= 1
        elif self.data_nascimento.month == self.data_nascimento.month > dt.datetime.today().date().month and self.data_nascimento.day > dt.datetime.today().date().day:
            idade -= 1
        return idade

    def comparar_altura(self, pessoa):
        if pessoa.altura > self.altura:
            return f"É mais baixo que {pessoa.nome}!"
        elif pessoa.altura < self.altura:
            return f"É mais alto que {pessoa.nome}!"
        elif pessoa.nome.capitalize == "Cristina":
            return f"És sempre mais baixa, {pessoa.nome}"
        else:
            return f"Empate!"
