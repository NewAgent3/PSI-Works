from veiculo import Veiculo


class Carro(Veiculo):
    def __init__(self, marca, modelo, n_portas):
        super().__init__(marca, modelo)
        self.n_portas = n_portas

    def descricao(self):
        return f"Marca: {self.marca} | Modelo: {self.modelo} | Nº Portas: {self.n_portas}"
