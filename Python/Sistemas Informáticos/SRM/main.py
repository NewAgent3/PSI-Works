from classes import SistemaCRM, Encomenda, Item, Fornecedor, Produto
import datetime as dt
empresa = SistemaCRM()
oasis = Fornecedor("A01", "Oasis", "219876543",
                   "oasis@hotmail.com", 50, 75, [])
worten = Fornecedor("9XY", "Worten", "210155222", "forn@worten.pt", 69, 55, [])
pc_componentes = Fornecedor("E23", "Pc Componentes",
                            "300600861", "enc@pccomponentes.com", 86, 80, [])
empresa.adicionar_fornecedor(oasis)
empresa.adicionar_fornecedor(worten)
empresa.adicionar_fornecedor(pc_componentes)
air_pods = Produto("MFHP4", "Apple AirPods", "Áudio", 219)
charger_asus = Produto("P7933", "Carregador Asus", "Peças Informática", 122.58)
teclado = Produto("S539", "Teclado Gaming", "Acessórios Gaming", 16.99)
empresa.adicionar_produto(air_pods)
empresa.adicionar_produto(charger_asus)
empresa.adicionar_produto(teclado)
item1 = Item(charger_asus, 20)
encomenda1 = Encomenda(1, dt.date(2026, 3, 22), worten, item1)
item2 = Item(air_pods, 50)
encomenda2 = Encomenda(1, dt.date(2026, 3, 22), worten, item2)
item3 = Item(teclado, 100)
encomenda3 = Encomenda(2, dt.date(2026, 3, 26), pc_componentes, item3)
item4 = Item(charger_asus, 10)
encomenda4 = Encomenda(3, dt.date(2026, 3, 28), oasis, item4)
empresa.adicionar_encomenda(encomenda1)
empresa.adicionar_encomenda(encomenda2)
empresa.adicionar_encomenda(encomenda3)
empresa.adicionar_encomenda(encomenda4)
print(oasis.avaliacao_total())
print(worten.avaliacao_total())
print(pc_componentes.avaliacao_total(), "\n")
for fornecedor in empresa.lista_fornecedores:
    print(f"{fornecedor.codigo} | {fornecedor.nome} | {fornecedor.contacto}")
for encomenda in empresa.lista_encomendas:
    print(f"\n=== Encomenda {encomenda.numero} ===")
    print(
        f"Data de entrega: {dt.datetime.strftime(encomenda.data, "%Y-%m-%d")}")
    print(f"{encomenda.itens.produto.codigo} | {encomenda.itens.produto.nome} | {encomenda.itens.produto.categoria} | {encomenda.itens.produto.preco}")
while True:
    try:
        codigo = int(input("\nCódigo do produto: "))
    except ValueError:
        print("Apenas pode usar números aqui!")
    else:
        break
while True:
    nome = input("Nome do produto: ")
    if nome.isalpha() == False:
        print("Apenas pode usar letras aqui!")
    else:
        break
while True:
    categoria = input("Categoria do produto: ")
    if categoria.isalpha() == False:
        print("Apenas pode usar letras aqui!")
    else:
        break
while True:
    try:
        preco = float(input("Preço do produto: "))
    except ValueError:
        print("Apenas pode usar números aqui!")
    else:
        break
ugp = Produto(codigo, nome, categoria, preco)
