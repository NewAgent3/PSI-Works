vendas = [250, 300, 150, 400, 500, 200, 350]
num_vendas = 0
print(sum(vendas))
for num in vendas:
    if num > 300:
        num_vendas += 1
print(num_vendas)
print(sum(vendas) / len(vendas))
vendas.remove(min(vendas))
valor = int(input("Novo valor: "))
vendas[vendas.index(max(vendas))] = valor
