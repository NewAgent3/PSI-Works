from veiculo import Veiculo


class Motociclo(Veiculo):
    def __init__(self, matricula, marca, custo_manuntencao, cc):
        super().__init__(matricula, marca, custo_manuntencao)
        self.cilindrada = cc
        self.taxa_desgaste = 50

    def calcular_manuntencao(self):
        return super().calcular_manuntencao() + self.taxa_desgaste

    def calcular_manuntencao_iva(self):  # Não tava bem calculado
        return self.calcular_manuntencao() * 1.23

    def __str__(self):
        return f"Matrícula: {self.matricula} | Marca: {self.marca} | Custo Manuntenção: {self.custo_manuntencao} | Cilindrada: {self.cilindrada}"
