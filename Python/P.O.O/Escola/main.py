import Aluno as al
import os
os.system("cls")
lista_alunos = []
loop = 0
validacao = False
while loop <= 1:
    loop += 1
    nome = input(f"Nome ({loop}): ")
    idade = int(input(f"Idade ({loop}): "))
    curso = input(f"Curso ({loop}): ")
    aluno = al.Aluno(nome, idade, curso)
    lista_alunos.append(aluno)
    print(f"Aluno {loop} criado!\n")
print("\nAdicionar notas ao Aluno 1:\n")
loop = 0
while loop <= 2:
    loop += 1
    nota = int(input(f"Nota ({loop}): "))
    while validacao == False:
        if nota > 20 or nota < 0:
            nota = int(input(f"Nota ({loop}) inválida: "))
        else:
            validacao == True
            break
    lista_alunos[0].adicionar_nota(nota)
validacao == False
print(f"\nA melhor nota do aluno 1 é {lista_alunos[0].mostrar_melhor_nota()}")
nova_idade = 18
lista_alunos[1].atualizar_idade(nova_idade)
print(f"\nMédia do aluno 1: {round(lista_alunos[0].calcular_media(), 1)}")
print("\nAdicionar notas ao Aluno 2:\n")
loop = 0
while loop <= 2:
    loop += 1
    nota = int(input(f"Nota ({loop}): "))
    while validacao == False:
        if nota > 20 or nota < 0:
            nota = int(input(f"Nota ({loop}) inválida: "))
        else:
            validacao == True
            break
    lista_alunos[1].adicionar_nota(nota)
validacao == False
lista_alunos[0].mostrar_informacoes()
lista_alunos[1].mostrar_informacoes()
