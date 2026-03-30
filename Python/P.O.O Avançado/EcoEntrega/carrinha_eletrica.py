from veiculo import Veiculo


class CarrinhaEletrica(Veiculo):
    def __init__(self, matricula, marca, custo_manuntencao, capacidade_bateria, autonomia_max):
        super().__init__(matricula, marca, custo_manuntencao)
        self.capacidade_bateria = capacidade_bateria
        self.autonomia_max = autonomia_max
        self.incentivo_fiscal = 150

    def calcular_manuntencao(self):
        return super().calcular_manuntencao() - self.incentivo_fiscal

    def calcular_manuntencao_iva(self):  # Não tava bem calculado
        return self.calcular_manuntencao() * 1.23

    def __str__(self):
        return f"Matrícula: {self.matricula} | Marca: {self.marca} | Custo Manuntenção: {self.custo_manuntencao} | Capacidade Bateria: {self.capacidade_bateria} | Autonomia Máxima: {self.autonomia_max}"
