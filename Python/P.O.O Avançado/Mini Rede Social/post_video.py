from post import Post


class PostVideo(Post):
    def __init__(self, utilizador, conteudo, url):
        super().__init__(utilizador, conteudo)
        self.url_video = url
