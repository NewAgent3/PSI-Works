import datetime as dt


class Motorista:
    def __init__(self, nome, num_carta_conducao, data):
        self.nome = nome
        self.num_carta_conducao = num_carta_conducao
        self.data_carta_conducao = dt.datetime.strptime(data, "%d/%m/%Y")

    # Tava invertido e supostamente antes dava errado...
    def calcular_anos_conducao(self):
        data_atual = dt.date.today()
        anos_conducao = data_atual.year - self.data_carta_conducao.year
        if (data_atual.month, data_atual.day) < (self.data_carta_conducao.month, self.data_carta_conducao.day):
            anos_conducao -= 1
        return anos_conducao

    def __str__(self):
        return f"Nome: {self.nome} | Nº Carta Condução: {self.num_carta_conducao} | Data da Carta Condução: {self.data_carta_conducao.day}/{self.data_carta_conducao.month}/{self.data_carta_conducao.year}"
