class Loja:
    def __init__(self):
        self.lista_funcionarios = []
        self.lista_produtos = []
        self.clientes_registrados = []
        self.lista_vendas = []

    def adicionar_funcionario(self, novo_funcionario):
        self.lista_funcionarios.append(novo_funcionario)

    def adicionar_produto(self, novo_produto):
        self.lista_produtos.append(novo_produto)

    def registrar_cliente(self, novo_cliente):
        self.clientes_registrados.append(novo_cliente)

    def registrar_venda(self, venda):
        self.lista_vendas.append(venda)
