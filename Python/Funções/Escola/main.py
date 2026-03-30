import aluno as al
import notas as ns
import os
os.system("cls")
validacao = False
num = 1
nome = input("Nome do aluno: ")
aluno = al.criar_aluno(nome)
while num <= 3:
    nota = int(input(f"Nota {num}: "))
    while validacao == False:
        if nota > 20 or nota < 0:
            nota = int(input(f"Nota {num} inválida: "))
        else:
            validacao = True
    aluno["Notas"] = ns.adicionar_nota(nota, aluno)
    num += 1
    validacao = False
print(f"\nAluno:\n{al.mostrar_dados(aluno)}")
print(f"Média final: {round(ns.calcular_media(aluno), 1)}")
if round(ns.calcular_media(aluno), 1) >= 10:
    print("\nAPROVADO!!!")
else:
    print("\nREPROVADO!!!")
