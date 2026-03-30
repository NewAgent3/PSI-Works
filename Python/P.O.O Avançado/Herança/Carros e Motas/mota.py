from veiculo import Veiculo


class Mota(Veiculo):
    def __init__(self, marca, modelo, cilindrada):
        super().__init__(marca, modelo)
        self.cilindrada = cilindrada

    def descricao(self):
        return f"Marca: {self.marca} | Modelo: {self.modelo} | Cilindrada: {self.cilindrada}cc"
