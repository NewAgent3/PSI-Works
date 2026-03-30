try:
    num1 = int(input("Num 1: "))
    num2 = int(input("Num 2: "))
    resultado = num1/num2
except ZeroDivisionError:
    print("Não se pode dividir por zero, macaco!")
except ValueError:
    print("Seu macaco, não podes por isso num numero inteiro!")
else:
    print(resultado)
finally:
    print("Operação terminada")
