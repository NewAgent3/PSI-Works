class Produto:
    def __init__(self, nome, preco, categoria):
        self.nome = nome
        self.preco = preco
        self.categoria = categoria
        self.stock_min = 1
        self.stock_max = 10

    def alterar_stock_min(self, novo_stock):
        self.stock_min = novo_stock

    def alterar_stock_max(self, novo_stock):
        self.stock_max = novo_stock
