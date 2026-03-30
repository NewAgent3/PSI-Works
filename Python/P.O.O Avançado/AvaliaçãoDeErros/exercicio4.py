class NumeroMuitoGrandeError(Exception):
    pass  # Número não pode ser maior que um X


class NumeroNegativoError(Exception):
    pass  # Número não pode ser negativo


nota = int(input("Nota de PSI: "))
try:
    if nota > 20:
        raise NumeroMuitoGrandeError("Nota é maior que 20!")
    elif nota < 0:
        raise NumeroNegativoError("Nota é negativa!")
    elif not (nota <= 20 and nota >= 10):
        print("Nota inválida! Recusada pelo professor!")
    else:
        print("Nota válida! Aceite pelo professor!")
except NumeroMuitoGrandeError:
    print("Número maior que o esperado!")
except NumeroNegativoError:
    print("Número negativo!")
