import matplotlib.pyplot as plot
from matplotlib.axes import Axes
import datetime as dt
tarefas = [{"Nome": "Verificação", "Inicio": "2026-06-04", "Duração": 1},
           {"Nome": "Reparação de Hardware", "Inicio": "2026-06-05", "Duração": 4},
           {"Nome": "Análise Problemas Software",
               "Inicio": "2026-06-05", "Duração": 2},
           {"Nome": "Instalação Configuração Programas Necessários",
               "Inicio": "2026-06-07", "Duração": 3},
           {"Nome": "Encomenda Peças em Falta",
               "Inicio": "2026-06-09", "Duração": 5},
           {"Nome": "Instalação Novos Componentes",
               "Inicio": "2026-06-14", "Duração": 2},
           {"Nome": "Config. Final Testes Sistema", "Inicio": "2026-06-16", "Duração": 2}]

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
