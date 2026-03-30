from veiculo import Veiculo


class Camiao(Veiculo):
    def __init__(self, matricula, marca, custo_manuntencao, capacidade_carga, num_eixos):
        super().__init__(matricula, marca, custo_manuntencao)
        self.capacidade_carga = capacidade_carga
        self.num_eixos = num_eixos
        self.custo_extra_eixo = 100

    def calcular_manuntencao(self):
        return super().calcular_manuntencao() + (100 * self.num_eixos)

    def calcular_manuntencao_iva(self):  # Não tava bem calculado
        return self.calcular_manuntencao() * 1.23

    def __str__(self):
        return f"Matrícula: {self.matricula} | Marca: {self.marca} | Custo Manuntenção: {self.custo_manuntencao} | Capacidade Carga: {self.capacidade_carga} | Nº Eixos: {self.num_eixos}"
