import random as rd


class Venda:
    def __init__(self, produtos, vendedor, cliente):
        self.id_fatura = rd.randint(1, 9999999)
        self.produtos = produtos
        self.vendedor = vendedor
        self.cliente = cliente

    def fazer_fatura(self):
        total = 0
        print(f"=== Fatura Nº {self.id_fatura} ===")
        print("- Produtos:")
        for produto in self.produtos:
            print(f"{produto.nome} - {produto.preco}")
            total += produto.preco
        print(f"\nTotal: {total}")
        print(f"Vendedor: {self.vendedor.nome}")
        print(f"Cliente: {self.cliente.nome}")
        print("\n=========================")
