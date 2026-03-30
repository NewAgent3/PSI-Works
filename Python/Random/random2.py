import random as rd
lista = "pedra", "papel", "tesoura"
escolha = input("Pedra, papel, ou tesoura?\n\nOpção: ").lower().strip(" ")
jogada_pc = rd.choice(lista)
match escolha:
    case "pedra":
        if jogada_pc == escolha:
            print("Empate!")
        elif jogada_pc == "papel":
            print("Perdeste...")
        elif jogada_pc == "tesoura":
            print("Ganhaste!!!")
    case "papel":
        if jogada_pc == escolha:
            print("Empate!")
        elif jogada_pc == "tesoura":
            print("Perdeste...")
        elif jogada_pc == "pedra":
            print("Ganhaste!!!")
    case "tesoura":
        if jogada_pc == escolha:
            print("Empate!")
        elif jogada_pc == "pedra":
            print("Perdeste...")
        elif jogada_pc == "papel":
            print("Ganhaste!!!")
    case _:
        print("Escolha inválida!!!")
        quit()
print(
    f"\nEscolha do AI: {jogada_pc.capitalize()}\nEscolha do user: {escolha.capitalize()}")
