class Produto:
    def __init__(self, nome, consumo_diario, tempo_reposicao, lote_aproveitamento):
        self.nome = nome
        self.consumo_diario = consumo_diario
        self.tempo_reposicao = tempo_reposicao
        self.lote_aproveitamento = lote_aproveitamento
        self.tempo_seguranca = 4

    def stock_minimo(self):
        return self.consumo_diario * self.tempo_seguranca

    def ponto_encomenda(self):
        return (self.consumo_diario * self.tempo_reposicao) + self.stock_minimo()

    def stock_maximo(self):
        return self.stock_minimo() + self.lote_aproveitamento

    def stock_medio(self):
        return (self.stock_maximo() + self.stock_minimo()) / 2

    def stock_ativo(self):
        return self.stock_medio() - self.stock_minimo()

    def __str__(self):
        return f"=== {self.nome} ===\nConsumo diário: {self.consumo_diario}\nLote aprovisionamento: {self.lote_aproveitamento}\nTempo de reposição: {self.tempo_reposicao} dias\nTempo de segurança: {self.tempo_seguranca} dias\nStock mínimo: {self.stock_minimo()}\nPonto de encomenta: {self.ponto_encomenda()}\nStock máximo: {self.stock_maximo()}\nStock médio: {self.stock_medio()}\nStock ativo: {self.stock_ativo()}\n"
