class TamanhoPostInvalidoError(Exception):
    pass  # Tamanho do post não pode ser maior que X


post = input("Post: ")
try:
    if len(post) < 10:
        raise TamanhoPostInvalidoError(
            "Post tem de ser maior que 10 carateres!")
    elif len(post) > 200:
        raise TamanhoPostInvalidoError(
            "Post tem de ser menor que 200 carateres!")
    else:
        print("Post criado!")
except TamanhoPostInvalidoError:
    print("Post maior que 200 ou menor que 10 carateres!")
