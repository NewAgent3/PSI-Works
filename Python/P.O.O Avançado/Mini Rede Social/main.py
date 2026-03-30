from utilizador import Utilizador
from comentario import Comentario
from post import Post
from post_video import PostVideo
from os import system
import colorama as cl
system("cls")
print(f"{cl.Style.BRIGHT}{cl.Fore.YELLOW}TITIO{cl.Fore.MAGENTA}GRAM{cl.Style.RESET_ALL}")
nome = input("Nome de Utilizador: ")
user1 = Utilizador(nome)
lista_posts = []
while True:
    system("cls")
    print("=" * 20)
    print(f"Utilizador atual: {user1.nome}")
    print("=" * 20)
    print("1 - Criar um Post")
    print("2 - Criar um Comentário")
    print("3 - Mostrar Informação de um Post")
    print("0 - Sair (SESSÃO NÃO GUARDA!)")
    while True:
        try:
            escolha = int(input("\nOpção: "))
        except BaseException:
            print("Opção Inválida!")
        else:
            system("cls")
            break
    match escolha:
        case 1:
            if len(lista_posts) < 1:
                print("Tipo de Post:")
                print("1 - Post Normal")
                print("2 - Post Vídeo")
                while True:
                    try:
                        escolha = int(input("\nOpção: "))
                    except BaseException:
                        print("Opção Inválida!")
                    else:
                        break
                match escolha:
                    case 1:
                        texto = input("Texto no Post: ")
                        post = Post(user1, texto)
                        lista_posts.append(post)
                    case 2:
                        texto = input("Texto no Post: ")
                        url = input("URL do vídeo: ")
                        post = PostVideo(user1, texto, url)
                        lista_posts.append(post)
                    case _:
                        continue
            else:
                print("Limite de posts exedido (Máximo de 1 por utilizador)!")
                input("\nPressione Enter para continuar...")
                pass
        case 2:
            if len(lista_posts) == 0:
                print("Não existem posts!")
                input("\nPressione Enter para continuar...")
                pass
            else:
                while True:
                    comentario = input("Comentário: ")
                    if comentario == "":
                        print("Comentário está vazio!")
                    else:
                        break
                comentario_final = Comentario(user1, comentario)
                lista_posts[0].adicionar_comentario(comentario_final)
        case 3:
            if len(lista_posts) == 0:
                print("Não existem posts!")
                input("\nPressione Enter para continuar...")
                pass
            else:
                print(lista_posts[0].autor.nome)
                print(lista_posts[0].conteudo)
                if hasattr(lista_posts[0], "url_video"):
                    print(lista_posts[0].url_video)
                if len(lista_posts[0].comentarios) == 0:
                    print("Não existem comentários de momento!")
                else:
                    for comentario in lista_posts[0].comentarios:
                        print(comentario)
                input("\nPressione Enter para continuar...")
        case 0:
            quit()
        case _:
            pass
