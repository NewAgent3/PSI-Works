import jogador as jd
import equipa as eq
import os
lebron = jd.Jogador(23, "LeBron James", 1984, "Extremo")
kevin = jd.Jogador(7, "Kevin Durant", 1988, "Extremo")
anthony = jd.Jogador(3, "Anthony Davis", 1993, "Poste")
james = jd.Jogador(13, "James Harden", 1989, "Extremo")
stephen = jd.Jogador(30, "Stephen Curry", 1988, "Extremo")
russell = jd.Jogador(5, "Russell Westbrook", 1988, "Base")
os.system("cls")
russell.alterar_numero(4)
celtics = eq.Equipa("Celtics", [lebron, kevin, anthony])
lakers = eq.Equipa("Lakers", [james, stephen, russell])
print(james, "\n")
print(celtics.mostrar_nome(), lakers.mostrar_nome(), "\n")
print(james.devolver_idade(), anthony.devolver_idade(), "\n")
print(celtics.mostrar_info(), "\n", lakers.mostrar_info())
stephen.alterar_posicao("Base")
print(celtics.mostrar_info(), "\n", lakers.mostrar_info())
