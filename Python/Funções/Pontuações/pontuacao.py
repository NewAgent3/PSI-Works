def adicionar_pontos(score_atual, pontos):
    return score_atual + pontos


def retirar_pontos(score_atual, pontos):
    return score_atual - pontos


def reset_pontos():
    return 0


def mais_pontos(jd, jd2):
    if jd["Pontuação"] == jd2["Pontuação"]:
        return 0
    elif jd["Pontuação"] > jd2["Pontuação"]:
        return jd
    else:
        return jd2
