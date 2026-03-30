from departamento import Departamento


class Cooperativa(Departamento):
    def __init__(self, nome, orcamento, numero_cooperantes):
        super().__init__(nome, orcamento)
        self.numero_cooperantes = numero_cooperantes

    def tipo_gestao(self):
        return self.numero_cooperantes
