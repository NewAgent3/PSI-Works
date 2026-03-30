from empresa import Empresa
from eni import ENI
from lda import Lda
from sa import SA
from cooperativa import Cooperativa
from socio import Socio
import datetime as dt
while True:
    try:
        nome = input("Nome da Empresa: ")
        localizacao = input("Localização da Empresa: ")
        data_criacao = input("Data de Criação da Empresa (Dia/Mês/Ano): ")
        numero_funcionarios = int(input("Número de Funcionários da Empresa: "))
        tipo_empresa = input(
            "Tipo de empresa: ").capitalize().strip(" ")
    except BaseException:
        pass
    else:
        empresa = Empresa(nome, localizacao, dt.datetime.strptime(
            data_criacao, "%d/%m/%Y"), numero_funcionarios)
        empresa.lista_departamentos.append(tipo_empresa)
        break
print("\n")
print(empresa.calcular_idade())
print(f"\n{empresa.nome}\n{empresa.localizacao}\n{data_criacao}\n{empresa.classificar_dimensao()}\nForma Jurídica:\n")
if len(empresa.lista_departamentos) == 0:
    print("Não existe registros!")
else:
    for departamento in empresa.lista_departamentos:
        print(departamento)
