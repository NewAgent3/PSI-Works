nomes = ["Ana", "Rui", "Ana", "Maria", "Rui"]


def nomes_unicos(nomes):
    set_nomes = set(nomes)
    num_repetidos = (len(nomes) - len(set_nomes))
    return set_nomes, num_repetidos


print(f"{nomes_unicos(nomes)[0]} | {nomes_unicos(nomes)[1]}")
