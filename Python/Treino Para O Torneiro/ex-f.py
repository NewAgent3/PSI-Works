ano = int(input())
if ano % 400 == 0 or ano % 4 == 0 and ano % 100 != 0:
    valor = 1
else:
    valor = 0
print(valor)
