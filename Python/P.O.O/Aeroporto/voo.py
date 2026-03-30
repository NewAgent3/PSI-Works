class Voo:
    def __init__(self, data, local_partida, local_destino):
        self.data = data
        self.local_partida = local_partida
        self.local_destino = local_destino
        self.lista_pilotos = []
        self.aviao_voo = None

    def adicionar_piloto(self, p):
        self.lista_pilotos.append(p)

    def atribuir_aviao(self, a):
        self.aviao_voo = a

    def mostrar_data(self):
        return self.data

    def mudar_partida(self, novo_local):
        self.local_partida = novo_local

    def mudar_destino(self, novo_local):
        self.local_destino = novo_local

    def __str__(self):
        piloto_dados = []
        for p in self.lista_pilotos:
            piloto_dados.append(p.nome)
            piloto_dados.append(p.brevet)
            piloto_dados.append(p.ano_nascimento)
        return f"{self.data}\n{self.local_partida}\n{self.local_destino}\n{piloto_dados}\n{self.aviao_voo}"
