class Empresa:
    def __init__(self):
        self.lista_motoristas = []
        self.lista_veiculos = []
        self.lista_entregas = []

    def adicionar_motorista(self, novo_motorista):
        self.lista_motoristas.append(novo_motorista)

    def remover_motorista(self, nome_motorista):
        for motorista in self.lista_motoristas:
            if motorista.nome == nome_motorista:
                self.lista_motoristas.remove(motorista)

    def adicionar_veiculo(self, novo_veiculo):
        self.lista_veiculos.append(novo_veiculo)

    def remover_veiculo(self, matricula_veiculo):
        for veiculo in self.lista_veiculos:
            if veiculo.matricula == matricula_veiculo:
                self.lista_veiculos.remove(veiculo)

    def registar_entrega(self, entrega):
        self.lista_entregas.append(entrega)

    def listar_entregas(self):
        # Vale mais a pena só usar o __str__ da entrega... (┬┬﹏┬┬)
        for entrega in self.lista_entregas:
            print(entrega)

    def __str__(self):
        nomes_motorista = []
        matricula_veiculo = []
        codigo_entrega = []
        for motorista in self.lista_motoristas:
            nomes_motorista.append(motorista.nome)
        for veiculo in self.lista_veiculos:
            matricula_veiculo.append(veiculo.matricula)
        for entrega in self.lista_entregas:
            codigo_entrega.append(entrega.codigo)
        return f"{nomes_motorista} | {matricula_veiculo} | {codigo_entrega}"
