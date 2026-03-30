from armazem import Armazem
from limpeza import Limpeza
from caixa import Caixa
from cliente import Cliente
from loja import Loja
from venda import Venda
from produto import Produto
from funcionario import Funcionario
loja1 = Loja()
caixa1 = Caixa("Abel", "Charneca Caparica", "219876543", "12/02/1990", 955)
limpeza1 = Limpeza("Fátima", "Almada", "961234567", "25/03/1966", 850, 8)
armazem1 = Armazem("Bruno", "Corroios", "910987654", "30/01/1981", 1012)
armazem1.alterar_acesso()
caixa2 = Caixa("Irene", "Costa Caparica", "924680246", "04/03/2000", 980)
loja1.adicionar_funcionario(caixa1)
loja1.adicionar_funcionario(caixa2)
loja1.adicionar_funcionario(limpeza1)
loja1.adicionar_funcionario(armazem1)
cliente1 = Cliente("Paulo", "Sobreda Caparica", "960987654", 1111)
cliente2 = Cliente("Rita", "Almada", "914680235", 9753)
loja1.registrar_cliente(cliente1)
loja1.registrar_cliente(cliente2)
nome = input("Nome do novo funcionário (Área de Limpeza): ")
morada = input("Morada do novo funcionário (Área de Limpeza): ")
numtelefone = input(
    "Número de telefone do novo funcionário (Área de Limpeza): ")
data_nascimento = input(
    "Data de nascimento (dia/mês/ano) do novo funcionário (Área de Limpeza): ")
base_salario = input("Salário base do novo funcionário (Área de Limpeza): ")
limpeza2 = Limpeza(nome, morada, numtelefone, data_nascimento, base_salario, 0)
loja1.adicionar_funcionario(limpeza2)
print(caixa1.calcular_salario_liquido())
print(limpeza1.calcular_salario_liquido())
armazem1.alterar_acesso()
print(caixa1.calcular_idade())
print(limpeza1.calcular_idade())
print(armazem1.calcular_idade())
print(caixa2.calcular_idade())
funcionario_maisvelho = Funcionario(
    "Free Use", "Free Use", "Free Use", "31/12/9999", 0)
for funcionario in loja1.lista_funcionarios:
    if funcionario.calcular_idade() > funcionario_maisvelho.calcular_idade():
        funcionario_maisvelho = funcionario
print(funcionario_maisvelho.nome)
print(funcionario_maisvelho.telefone)
produto1 = Produto("Powerbank", 25.90, "Informática")
produto2 = Produto("Estendal Roupa", 27.43, "Lar")
produto3 = Produto("Bola Basket", 10.16, "Desporto")
produto4 = Produto("Rato Gaming", 19.99, "Informática")
loja1.adicionar_produto(produto1)
loja1.adicionar_produto(produto2)
loja1.adicionar_produto(produto3)
loja1.adicionar_produto(produto4)
fatura1 = Venda([produto1, produto4], caixa2, cliente1)
fatura1.fazer_fatura()
