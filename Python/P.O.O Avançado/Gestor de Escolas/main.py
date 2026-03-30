from funcionario import Funcionario
from disciplina import Disciplina
from professor import Professor
from curso import Curso
from aluno import Aluno

gpsi = Curso("GPSI")
disciplina1 = Disciplina("PSI", "segunda-feira", 222)
disciplina2 = Disciplina("SO", "quarta-feira", 92)
disciplina3 = Disciplina("Matemática", "quinta-feira", 100)
gpsi.adiconar_disciplina(disciplina1)
gpsi.adiconar_disciplina(disciplina2)
gpsi.adiconar_disciplina(disciplina3)
alvaro = Professor("Álvaro", "21/05/1980", 1.80, 1800, disciplina1)
carlos = Funcionario("Carlos", "10/03/1975", 1.68,
                     "Assistente Administrativo", 8)
joao = Aluno("João", "15/10/2010", 1.78, 30123, gpsi)
joao.adicionar_notas(14)
joao.adicionar_notas(12)
joao.adicionar_notas(10)

print("====== GESTÃO DA ESCOLA SECUNDÁRIA CACILHAS-TEJO ======\n")
print(
    f"Professor {alvaro.nome.capitalize()} | {alvaro.disciplina.nome} | Salário líquido: {alvaro.calcular_salario_liquido()}€")
print(f"Idade: {alvaro.calcular_idade()}\n")
print(
    f"Funcionário {carlos.nome.capitalize()} | {carlos.cargo} | Salário líquido: {carlos.calcular_salario_liquido()}€")
print(f"Idade: {carlos.calcular_idade()}\n")
print(
    f"Aluno {joao.n_processo} | {joao.nome} | Média: {round(joao.calcular_media(), 1)} | Estado: {joao.estado()}")
print(f"Idade: {joao.calcular_idade()}")
