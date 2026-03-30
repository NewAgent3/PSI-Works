from departamento import Departamento


class SA(Departamento):
    def __init__(self, nome, orcamento, capital_social, numero_acoes, lista_socios):
        super().__init__(nome, orcamento)
        self.capital_social = capital_social
        self.numero_acoes = numero_acoes
        self.lista_socios = lista_socios

    def pode_entrar_em_bolsa(self):
        if self.numero_acoes > 0:
            return True
        else:
            return False
