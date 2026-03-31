class SistemaCRM:
    def __init__(self):
        self.lista_fornecedores = []
        self.lista_produtos = []
        self.lista_encomendas = []

    def adicionar_fornecedor(self, fornecedor):
        self.lista_fornecedores.append(fornecedor)

    def adicionar_produto(self, produto):
        self.lista_produtos.append(produto)

    def adicionar_encomenda(self, encomenda):
        self.lista_encomendas.append(encomenda)


class Encomenda:
    def __init__(self, numero, data, fornecedor, itens):
        self.numero = numero
        self.data = data
        self.fornecedor = fornecedor
        self.itens = itens

    def calcular_total(self):
        total = 0
        for item in self.itens:
            total = item.calcular_total()
        return total


class Item:
    def __init__(self, produto, quantidade):
        self.produto = produto
        self.quantidade = quantidade

    def calcular_total(self):
        return self.produto.preco * self.quantidade


class Produto:
    def __init__(self, codigo, nome, categoria, preco):
        self.codigo = codigo
        self.nome = nome
        self.categoria = categoria
        self.preco = preco

    def __str__(self):
        return self.nome


class Fornecedor:
    def __init__(self, codigo, nome, contacto, email, avaliacao_qualidade, avaliacao_cumprimento_prazos, lista_produtos):
        self.codigo = codigo
        self.nome = nome
        self.contacto = contacto
        self.email = email
        self.avaliacao_qualidade = avaliacao_qualidade
        self.avaliacao_cumprimento_prazos = avaliacao_cumprimento_prazos
        self.lista_produtos = lista_produtos

    def avaliacao_total(self):
        return (self.avaliacao_qualidade + self.avaliacao_cumprimento_prazos) / 2

    def associar_produto(self, produto):
        self.lista_produtos.append(produto)

    def __str__(self):
        return self.nome
