class Post:
    def __init__(self, utilizador, conteudo):
        self.autor = utilizador
        self.conteudo = conteudo
        self.comentarios = []

    def adicionar_comentario(self, c):
        erro = False
        try:
            if c.texto == "":
                raise ValueError
            self.comentarios.append(c)
        except ValueError:
            print("Comentário não pode estar vazio!")
            erro = True
        finally:
            if erro != True:
                print("Comentário adicionado!")
            else:
                print("Comentário não adicionado!")

    def mostrar_comentarios(self):
        if len(self.comentarios) == 0:
            print("Não existe comentários!")
        else:
            print("Comentários:")
            for comentario in self.comentarios:
                print(f"{comentario.autor}: {comentario.texto}\n")
