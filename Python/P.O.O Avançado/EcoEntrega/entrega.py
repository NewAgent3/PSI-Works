import datetime as dt

class Entrega:
    def __init__(self, codigo, data, motorista, veiculo, distancia):
        self.codigo = codigo
        self.data = dt.datetime.strptime(data, "%d/%m/%Y")
        self.motorista = motorista
        self.veiculo = veiculo
        self.distancia = distancia
    def alterar_distancia(self, nova_distancia):
        self.distancia = nova_distancia
    def alterar_motorista(self, novo_motorista):
        self.motorista = novo_motorista
    def __str__(self):
        return f"Código: {self.codigo} | Data: {self.data.day}/{self.data.month}/{self.data.year} | Motorista: {self.motorista.nome} | Veículo: {self.veiculo.marca} | Distância: {self.distancia}km"