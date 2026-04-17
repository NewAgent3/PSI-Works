import matplotlib.pyplot as plot
from matplotlib.axes import Axes
import datetime as dt
tarefas = [{"Nome": "Definir Tema", "Inicio": "2026-05-12", "Duração": 3},
           {"Nome": "Reservar", "Inicio": "2026-05-15", "Duração": 5},
           {"Nome": "Promover", "Inicio": "2026-05-15", "Duração": 4},
           {"Nome": "Imprimir", "Inicio": "2026-05-19", "Duração": 2},
           {"Nome": "Montagem", "Inicio": "2026-05-21", "Duração": 3},
           {"Nome": "Evento e Arrumação", "Inicio": "2026-05-24", "Duração": 2}]

nomes = [nome["Nome"] for nome in tarefas]
datas = [dt.datetime.strptime(data["Inicio"], "%Y-%m-%d") for data in tarefas]
duracoes = [duracao["Duração"] for duracao in tarefas]
fig, ax = plot.subplots(figsize=(10, 5))
ax: Axes
for i, (inicio, duracao) in enumerate(zip(datas, duracoes)):
    ax.barh(nomes[i], duracao, left=inicio, height=0.6, color="blue")
ax.set_ylabel("Tarefas")
ax.set_xlabel("Datas")
ax.set_yticks(range(len(nomes)))
ax.set_yticklabels(nomes)
ax.invert_yaxis()
ax.set_title("Semana do Conhecimento")
plot.show()
