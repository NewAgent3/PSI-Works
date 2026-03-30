from departamento import Departamento


class Lda(Departamento):
    def __init__(self, nome, orcamento, capital_social, lista_socios):
        super().__init__(nome, orcamento)
        self.capital_social = capital_social
        self.lista_socios = lista_socios

    def responsabilidade(self):
        return "Responsabilidade Limitada ao Capital Social"
