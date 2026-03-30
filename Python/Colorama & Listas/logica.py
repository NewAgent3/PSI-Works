import math
salario = 700
bonus = 50
salario_total = salario + bonus
print(f"Salário total: {salario_total}")
print("\n", "*" * 50, "\n")
cartao_anopassado = int(input("Nº cartões do ano anterior: "))
alunos_matriculados = int(input("Nº alunos matriculados: "))
caixas_encomendar = math.ceil(alunos_matriculados / 100)
print(f"\nNº cartões necessários: {alunos_matriculados - cartao_anopassado}")
print(f"Caixas a encomendar: {caixas_encomendar}")
print(
    f"Nº cartões para o ano seguinte: {(caixas_encomendar * 100) - (alunos_matriculados - cartao_anopassado)}")
print("\n", "*" * 50, "\n")
passos = int(input("Nº de passos: "))
comp_passo = float(input("Comprimento dos passos: "))
lado = math.ceil((comp_passo / 3) * passos)
print(f"\nPerímetro: {lado * 4} metros")
print(f"Área: {lado * lado} m²")
