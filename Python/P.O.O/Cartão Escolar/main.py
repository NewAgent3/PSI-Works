import cartao_escolar as ce
import os
os.system("cls")
nome = input("Nome do aluno: ")
ano_turma = input("Ano e turma (Ex. 10ºA): ")
cartao = ce.Cartao(nome, ano_turma)
while True:
    os.system("cls")
    print("=== Cartão Escolar ===")
    print("1 - Ativar Cartão")
    print("2 - Entrada na Escola")
    print("3 - Saída na Escola")
    print("4 - Carregar Cartão")
    print("5 - Processar Compra")
    print("6 - Anular Cartão")
    print("7 - Ver Informação")
    print("0 - Sair")
    try:
        opcao = int(input("\nOpção: "))
        match opcao:
            case 1:
                if cartao.ativacao == True:
                    print("Cartão já está ativo!")
                else:
                    cartao.ativar_cartao()
                input("\nPressione Enter para continuar...")
            case 2:
                if cartao.ativacao == False or cartao.entrada == True:
                    print("Cartão não está ativo ou já está dentro da escola!")
                else:
                    cartao.entrada_escola()
                input("\nPressione Enter para continuar...")
            case 3:
                if cartao.ativacao == False or cartao.entrada == False:
                    print("Cartão não está ativo ou não está dentro da escola!")
                else:
                    cartao.saida_escola()
                input("\nPressione Enter para continuar...")
            case 4:
                if cartao.ativacao == False or cartao.entrada == False:
                    print("Cartão não está ativo ou não deu entrada!")
                else:
                    dinheiro = round(
                        float(input("Dinheiro para carregar: ")), 2)
                    cartao.carregar_cartao(dinheiro)
                input("\nPressione Enter para continuar...")
            case 5:
                if cartao.ativacao == False or cartao.entrada == False:
                    print("Cartão não está ativo ou não deu entrada!")
                else:
                    preco = round(float(input("Preço do item a comprar: ")), 2)
                    if cartao.processar_compra(preco) == False:
                        print("Saldo insuficiente!")
                    else:
                        cartao.processar_compra(preco)
                input("\nPressione Enter para continuar...")
            case 6:
                if cartao.ativacao == False:
                    print("Cartão já está anulado!")
                else:
                    cartao.anular_cartao()
                input("\nPressione Enter para continuar...")
            case 7:
                print(f"\nTitular: {cartao.aluno}")
                print(f"Ano e Turma: {cartao.ano_turma}")
                print(f"Saldo: {round(cartao.saldo, 2)}")
                print(f"Entrada na Escola: {cartao.entrada}")
                print(f"Ativação: {cartao.ativacao}")
                input("\nPressione Enter para continuar...")
            case 0:
                quit()
            case _:
                pass
    except ValueError:
        pass
