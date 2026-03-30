import random as rd
lista = []
while len(lista) <= 4:
    lista.append(rd.randint(1, 50))
print(lista)
lista_rand = rd.shuffle(lista)
print(lista)
