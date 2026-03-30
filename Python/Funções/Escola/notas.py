def adicionar_nota(nota, aluno):
    aluno["Notas"].append(nota)
    return aluno["Notas"]


def calcular_media(aluno):
    media = sum(aluno["Notas"]) / len(aluno["Notas"])
    return media
