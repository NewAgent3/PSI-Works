import matplotlib.pyplot as plot
import datetime as dt
tarefas = [{"Nome": "Definir Tema", "Inicio": "2026-05-12", "Duração": 3},
           {"Nome": "Reservar", "Inicio": "2026-05-15", "Duração": 5},
           {"Nome": "Promover", "Inicio": "2026-05-15", "Duração": 4},
           {"Nome": "Imprimir", "Inicio": "2026-05-19", "Duração": 2},
           {"Nome": "Montagem", "Inicio": "2026-05-21", "Duração": 3},
           {"Nome": "Evento e Arrumação", "Inicio": "2026-05-24", "Duração": 2}]
nomes = [nome["Nome"] for nome in tarefas]
datas = [dt.datetime.strptime(data["Inicio"], "%Y-%m-%d") for data in tarefas]
