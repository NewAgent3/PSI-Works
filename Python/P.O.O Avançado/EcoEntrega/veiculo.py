class Veiculo:
    def __init__(self, matricula, marca, custo_manuntencao):
        self.matricula = matricula
        self.marca = marca
        self.custo_manuntencao = custo_manuntencao
    def calcular_manuntencao(self):
        return self.custo_manuntencao
    def calcular_manuntencao_iva(self):
        return self.custo_manuntencao + (self.custo_manuntencao * 0.23)
    def comparar_custo_base(self, veiculo):
        if veiculo.custo_manuntencao > self.custo_manuntencao:
            return f"O {veiculo.marca} tem um maior custo de manuntenção!"
        elif veiculo.custo_manuntencao < self.custo_manuntencao:
            return f"O {veiculo.marca} tem um menor custo de manuntenção!"
        else:
            return "Ambos pagam os mesmos!"
    def __str__(self):
        return f"Matrícula: {self.matricula} | Marca: {self.marca} | Custo Manuntenção: {self.custo_manuntencao}"