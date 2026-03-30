from classes import RH, Funcionario, FuncionarioEfetivo, FuncionarioEstagiario, FuncionarioTempoParcial, Contrato, Ferias, RegistoAssiduidade
import datetime as dt
rh = RH()
# Funcionário: Ana Ribeiro
contrato_ana = Contrato(
    "Sem Termo", dt.datetime.strptime("01/03/2020", "%d/%m/%Y"))
assiduidade_ana = RegistoAssiduidade(1, 0, 5)
ferias_ana = Ferias(22, 5)
ana_ribeiro = FuncionarioEfetivo("Ana Ribeiro", 101, "Casada",
                                 1200, "Administrativa", contrato_ana, assiduidade_ana, ferias_ana)
rh.adicionar_funcionario(ana_ribeiro)
# Funcionário: Miguel Ferreira
contrato_miguel = ("Estágio", dt.datetime.strptime("15/01/2025", "%d/%m/%Y"))
assiduidade_miguel = RegistoAssiduidade(0, 2, 0)
ferias_miguel = Ferias(5, 1)
miguel_ferreira = FuncionarioEstagiario(
    "Miguel Ferreira", 205, "Solteiro", "Estagiário Informático", contrato_miguel, assiduidade_miguel, ferias_miguel)
rh.adicionar_funcionario(miguel_ferreira)
# Funcionário: Joana Martins
contrato_joana = Contrato(
    "Tempo Parcial", dt.datetime.strptime("01/09/2024", "%d/%m/%Y"))
assiduidade_joana = RegistoAssiduidade(0, 2, 0)
ferias_joana = Ferias(5, 1)
joana_martins = FuncionarioTempoParcial(
    "Joana Martins", 332, "União de Facto", "Técnica de Suporte", contrato_joana, assiduidade_joana, ferias_joana, 75)
rh.adicionar_funcionario(joana_martins)
# Salários Líquidos dos Funcionários
print(ana_ribeiro.calcular_salario_liquido())
print(miguel_ferreira.calcular_salario_liquido())
print(joana_martins.calcular_salario_liquido())
# Número de faltas e atrasos
print(ana_ribeiro.assiduidade.faltas)
print(ana_ribeiro.assiduidade.atrasos)
print(miguel_ferreira.assiduidade.faltas)
print(miguel_ferreira.assiduidade.atrasos)
print(joana_martins.assiduidade.faltas)
print(joana_martins.assiduidade.atrasos)
# Emitir Recibos
rh.emitir_recibo(ana_ribeiro)
rh.emitir_recibo(miguel_ferreira)
rh.emitir_recibo(joana_martins)
# Mostrar Estatísticas
rh.mostrar_estatisticas()
