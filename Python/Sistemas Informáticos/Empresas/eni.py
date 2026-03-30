from departamento import Departamento


class ENI(Departamento):
    def __init__(self, nome, orcamento, nif_pessoal):
        super().__init__(nome, orcamento)
        self.nif_pessoal = nif_pessoal

    def responsabilidade(self):
        return "Reponsabilidade Ilimitada do Empresário"
