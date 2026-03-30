class GolosInvalidosError(Exception):
    pass


while True:
    try:
        golo_a = int(input("Golos da equipa A: "))
        if golo_a < 0:
            raise GolosInvalidosError
        golo_b = int(input("Golos da equipa B: "))
        if golo_b < 0:
            raise GolosInvalidosError
    except GolosInvalidosError:
        print("Número de golos inválido!\n")
    except ValueError:
        print("Número de golos inválido!\n")
    else:
        break
if golo_a > golo_b:
    print("\nGanhou a equipa A!!!")
elif golo_b > golo_a:
    print("\nGanhou a equipa B!!!")
else:
    print("\nEmpate!!!")
