from entrega import Entrega
from camiao import Camiao
from carrinha_eletrica import CarrinhaEletrica
from motociclo import Motociclo
from empresa import Empresa
from motorista import Motorista
from veiculo import Veiculo
empresa = Empresa()
veiculo1 = Camiao("44-XX-00", "Volvo", 1200, 18, 4)
veiculo2 = CarrinhaEletrica("EL-22-AA", "Tesla", 500, 100, 400)
veiculo3 = Motociclo("MM-11-22", "Honda", 200, 500)
empresa.adicionar_veiculo(veiculo1)
empresa.adicionar_veiculo(veiculo2)
empresa.adicionar_veiculo(veiculo3)
motorista1 = Motorista("Ricardo Santos", "C-9988", "19/02/2018")
# Data de condução estava errada
motorista2 = Motorista("Beatriz Costa", "B-1122", "02/03/2022")
empresa.adicionar_motorista(motorista1)
empresa.adicionar_motorista(motorista2)
entrega1 = Entrega("E01", "20/01/2026", motorista1, veiculo1, 150)
entrega2 = Entrega("E02", "21/02/2026", motorista2, veiculo2, 45)
empresa.registar_entrega(entrega1)
empresa.registar_entrega(entrega2)
print("Entregas:")
empresa.listar_entregas()
print("\nManuntenção com IVA mais cara:")  # Não usei o método apropriado
if veiculo1.calcular_manuntencao_iva() > veiculo2.calcular_manuntencao_iva():
    print(f"Veículo com IVA mais caro: {veiculo1.marca}")
else:
    print(f"Veículo com IVA mais caro: {veiculo2.marca}")
print("Custo Manuntenção:")
for veiculo in empresa.lista_veiculos:
    print(veiculo.calcular_manuntencao())
print("\nAnos a conduzir:")
for motorista in empresa.lista_motoristas:
    print(motorista.calcular_anos_conducao())
