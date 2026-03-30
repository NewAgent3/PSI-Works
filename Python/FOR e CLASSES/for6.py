palavra = input("Palavra: ")
soma = 0
for letra in palavra:
    if letra in ["a", "e", "i", "o", "u"]:
        soma += 1
print(soma)
