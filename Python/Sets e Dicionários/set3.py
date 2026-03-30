lista1 = [1, 4, 6, 8]
lista2 = [3, 4, 7, 8]
lista1_set = set(lista1)
if lista1_set.intersection(lista2):
    print("Tem números em comum!")
    print(lista1_set.intersection(lista2))
else:
    print("Não tem números em comum!")
