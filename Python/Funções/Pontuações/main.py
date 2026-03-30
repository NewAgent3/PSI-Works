import os
import pontuacao as ptc
import jogador as jd
invalido = 0

os.system('cls' if os.name == 'nt' else 'clear')
nome = input("Nome do jogador: ")
jogador = jd.criar_jogador(nome)

while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== MENU ===\n1 - Adicionar pontos\n2 - Retirar pontos\n3 - Reset pontos\n4 - Mostrar jogador\n5 - Sair")
    if invalido == 1:
        opcao = int(input("Opção inválida: "))
        invalido = 0
    else:
        opcao = int(input("Opção: "))
    match(opcao):
        case 1:
            pontos = int(input("Pontuação a adicionar: "))
            jogador["Pontuação"] = ptc.adicionar_pontos(
                jogador["Pontuação"], pontos)
            print(f"Pontuação: {jogador['Pontuação']}")
            input("Feito! Pressione qualquer tecla para voltar...")
        case 2:
            pontos = int(input("Pontuação a retirar: "))
            if jogador["Pontuação"] - pontos < 0:
                jogador["Pontuação"] = 0
            else:
                jogador["Pontuação"] = ptc.retirar_pontos(
                    jogador["Pontuação"], pontos)
            print(f"Pontuação: {jogador['Pontuação']}")
            input("Feito! Pressione qualquer tecla para voltar...")
        case 3:
            jogador["Pontuação"] = ptc.reset_pontos()
            input("Feito! Pressione qualquer tecla para voltar...")
        case 4:
            print(jd.mostrar_jogador(jogador))
            input("Feito! Pressione qualquer tecla para voltar...")
        case 5:
            quit()
        case _:
            invalido = 1
