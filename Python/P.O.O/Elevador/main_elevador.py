import elevador as elv
import pessoa as pss
import os
import random as rd
os.system("cls")
elevador1 = elv.Elevador()
elevador2 = elv.Elevador()
lista_rand = []
for num in range(0, 2):
    nome = input(f"Nome (Passageiro {num + 1}): ")
    ano_nascimento = int(input(f"Ano de Nascimento (Passageiro {num + 1}): "))
    passageiro = pss.Pessoa(nome, ano_nascimento)
    elevador1.adicionar_passageiro(passageiro)
    print("-"*10)
    num += 1
for num in range(1, 3):
    nome = input(f"Nome (Passageiro {num + 2}): ")
    ano_nascimento = int(input(f"Ano de Nascimento (Passageiro {num + 2}): "))
    passageiro = pss.Pessoa(nome, ano_nascimento)
    elevador2.adicionar_passageiro(passageiro)
    print("-"*10)
    num += 1
lista_rand = elevador1.lista_passageiros + elevador2.lista_passageiros
elevador1.adicionar_passageiro(lista_rand[rd.randint(0, len(lista_rand) - 1)])
elevador2.adicionar_passageiro(lista_rand[rd.randint(0, len(lista_rand) - 1)])
input("Pressione Enter para continuar...")
os.system("cls")
elevador1.mudar_andar(7)
elevador2.mudar_andar(3)
elevador1.retorna_passageiros(True)
elevador2.retorna_passageiros(True)
input("Pressione Enter para continuar...")
os.system("cls")
mais_novo = None
for pessoa in lista_rand:
    if mais_novo == None or mais_novo.ano_nascimento <= pessoa.ano_nascimento:
        mais_novo = pessoa
print(f"Nome do mais novo: {mais_novo.nome}")
print(f"Ano de Nascimento do mais novo: {mais_novo.ano_nascimento}")
input("Pressione Enter para continuar...")
os.system("cls")
novo_nome = input("Novo nome: ")
elevador1.lista_passageiros[0].alterar_nome(novo_nome)
input("Pressione Enter para continuar...")
os.system("cls")
elevador1.retorna_passageiros(False)
elevador2.retorna_passageiros(False)
input("Pressione Enter para continuar...")
os.system("cls")
elevador1.remover_passageiro(0)
elevador2.remover_passageiro(0)
elevador1.retorna_passageiros(True)
elevador2.retorna_passageiros(True)
input("Pressione Enter para continuar...")
os.system("cls")
elevador1.remover_todos()
elevador2.remover_todos()
elevador1.retorna_passageiros(True)
elevador2.retorna_passageiros(True)
input("Pressione Enter para continuar...")
os.system("cls")
