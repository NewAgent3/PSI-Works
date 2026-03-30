tupla = (10, 20, 30, 10, 40, 10, 50)
print(f"O número 10 aparece {tupla.count(10)} vezes")
print(
    f"O número 40 aparece pela primeira vez na posição {tupla.index(40) + 1}")
if 60 in tupla:
    print("O número 60 está na tupla!")
else:
    print("O número 60 não está na tupla!")
