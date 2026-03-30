cores = {"azul", "verde", "vermelho"}
cores.add("amarelo")
cores.remove("verde")
cor = input("Diga uma cor: ")
if cor in cores:
    print(f"A cor {cor.capitalize()} está no set!")
else:
    print(f"A cor {cor.capitalize()} não está no set!")
