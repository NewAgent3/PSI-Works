import matplotlib.pyplot as plot
from matplotlib.axes import Axes
import datetime as dt
tarefas = [{"Nome": "Definir Catálogo", "Inicio": "2026-06-15", "Duração": 4},
           {"Nome": "Desenvolvimento do Website",
               "Inicio": "2026-06-19", "Duração": 7},
           {"Nome": "Identidade da Marca", "Inicio": "2026-06-19", "Duração": 3},
           {"Nome": "Integração Visual", "Inicio": "2026-06-22", "Duração": 2},
           {"Nome": "Configurar Metodos de Pagamento",
               "Inicio": "2026-06-24", "Duração": 3},
           {"Nome": "Divulgação Inicial", "Inicio": "2026-06-27", "Duração": 2}]

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
ax.set_title("Loja online de Artesanato")
plot.show()
