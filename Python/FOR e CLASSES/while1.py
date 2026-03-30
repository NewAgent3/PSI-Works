lista = []
num = int(input("Sair = 0 | Número: "))
lista.append(num)
while num != 0:
    num = int(input("Sair = 0 | Número: "))
    lista.append(num)
print(sum(lista))
