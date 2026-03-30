import os
import pontuacao as ptc
import jogador as jd
invalido = 0

os.system('cls' if os.name == 'nt' else 'clear')
nome = input("Nome do jogador: ")
jogador = jd.criar_jogador(nome)
nome = input("Nome do segundo jogador: ")
segundo_jogador = jd.criar_jogador(nome)
lista_jogadores = [jogador, segundo_jogador]
while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== MENU ===\n1 - Adicionar pontos\n2 - Retirar pontos\n3 - Reset pontos\n4 - Mostrar jogador\n5 - Maior número de pontos\n6 - Sair\n")
    if invalido == 1:
        opcao = int(input("Opção inválida: "))
        invalido = 0
    else:
        opcao = int(input("Opção: "))
    match(opcao):
        case 1:
            op_jogador = int(
                input(f"Qual é o jogador:\n1 - {lista_jogadores[0]}\n2 - {lista_jogadores[1]}\n\nOpção: ")) - 1
            pontos = int(input("Pontuação a adicionar: "))
            lista_jogadores[op_jogador]['Pontuação'] = ptc.adicionar_pontos(
                lista_jogadores[op_jogador]['Pontuação'], pontos)
            print(
                f"Pontuação nova: {lista_jogadores[op_jogador]['Pontuação']}")
            input("Feito! Pressione qualquer tecla para voltar...")
        case 2:
            op_jogador = int(
                input(f"Qual é o jogador:\n1 - {lista_jogadores[0]}\n2 - {lista_jogadores[1]}\n\nOpção: ")) - 1
            pontos = int(input("Pontuação a retirar: "))
            if lista_jogadores[op_jogador]['Pontuação'] - pontos < 0:
                lista_jogadores[op_jogador]['Pontuação'] = 0
            else:
                lista_jogadores[op_jogador]['Pontuação'] = ptc.retirar_pontos(
                    lista_jogadores[op_jogador]['Pontuação'], pontos)
            print(f"Pontuação: {lista_jogadores[op_jogador]['Pontuação']}")
            input("Feito! Pressione qualquer tecla para voltar...")
        case 3:
            op_jogador = int(
                input(f"Qual é o jogador:\n1 - {lista_jogadores[0]}\n2 - {lista_jogadores[1]}\n\nOpção: ")) - 1
            lista_jogadores[op_jogador]['Pontuação'] = ptc.reset_pontos()
            input("Feito! Pressione qualquer tecla para voltar...")
        case 4:
            print(jd.mostrar_jogadores(lista_jogadores[0], lista_jogadores[1]))
            input("Feito! Pressione qualquer tecla para voltar...")
        case 5:
            if ptc.mais_pontos(lista_jogadores[0], lista_jogadores[1]) == 0:
                print(
                    f"Ambos têm a mesma pontuação ({lista_jogadores[0]["Pontuação"]})")
            else:
                print(
                    f"O jogador com mais pontos é {ptc.mais_pontos(lista_jogadores[0], lista_jogadores[1])}")
            input("Feito! Pressione qualquer tecla para voltar...")
        case 6:
            quit()
        case _:
            invalido = 1
