import colorama as clr
import os

lista_contactos = []
valido = False


def menu():
    print(clr.Fore.BLUE)
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*5, "GESTOR DE CONTACTOS",
          "="*5, clr.Style.RESET_ALL)
    print("1 - Adicionar contacto")
    print("2 - Pesquisar contacto")
    print("3 - Listar por categoria")
    print("4 - Estatísticas")
    print("5 - Frase automática", clr.Fore.RED)
    print("0 - Sair", clr.Style.RESET_ALL)
    print("="*31)
    escolha = int(input("\nInput: "))
    match escolha:
        case 1:
            adicionar_contacto(lista_contactos, valido)
        case 2:
            pesquisar_contacto(lista_contactos)
        case 3:
            listar_contactos(lista_contactos)
        case 4:
            estatistica(lista_contactos)
        case 5:
            frase_automatica(lista_contactos)
        case 0:
            os.system('cls' if os.name == 'nt' else 'clear')
            quit()


def adicionar_contacto(lista_contactos, valido):
    if len(lista_contactos) > 4:
        print("Número de contactos excedido!")
        input("Pressione Enter para voltar...")
        menu()
    nome = input("\nNome: ")
    idade = int(input("Idade: "))
    while valido == False:
        if idade < 0 or idade > 120:
            idade = int(input("Idade inválida! | Idade: "))
        else:
            valido = True
            pass
    valido = False
    telefone = int(input("Número de telefone: "))
    while valido == False:
        if len(str(telefone)) != 9:
            telefone = int(
                input("Número de telefone inválida! | Número de telefone: "))
        else:
            valido = True
            pass
    valido = False
    email = input("E-Mail: ")
    while valido == False:
        if "@" not in email and (".com" not in email or ".org" not in email):
            email = input("E-Mail inválido! | E-Mail: ")
        else:
            valido = True
            pass
    valido = False
    categoria = int(
        input("\n1 - Família\n2 - Amigos\n3 - Trabalho\n\nInput: "))
    while valido == False:
        if categoria not in [1, 2, 3]:
            categoria = input(
                "Categoria inválida!\n\n1 - Família\n2 - Amigos\n3 - Trabalho\n\nInput: ")
        else:
            valido = True
            pass
    valido = False
    contacto = {
        "nome": nome,
        "idade": idade,
        "telefone": telefone,
        "email": email,
        "categoria": categoria
    }
    lista_contactos.append(contacto)
    return lista_contactos and menu()


def pesquisar_contacto(lista_contactos):
    if len(lista_contactos) == 0:
        print("Não existem contactos!")
        input("Pressione Enter para voltar...")
        menu()
    nome = input("\nNome a pesquisar: ")
    for contacto in lista_contactos:
        if contacto["nome"].lower() == nome.lower():
            print(f"Nome: {contacto['nome']}")
            print(f"Idade: {contacto['idade']}")
            print(f"Telefone: {contacto['telefone']}")
            print(f"E-Mail: {contacto['email']}")
            categorias = {1: "Família", 2: "Amigos", 3: "Trabalho"}
            print(f"Categoria: {categorias[contacto['categoria']]}")
            break
        else:
            print("\nContacto não encontrado!")
    input("\nPressione Enter para voltar ao menu...")
    return menu()


def listar_contactos(lista_contactos):
    if len(lista_contactos) == 0:
        print("Não existem contactos!")
        input("Pressione Enter para voltar...")
        menu()
    categoria = int(
        input("1 - Família\n2 - Amigos\n3 - Trabalho\n\nCategoria a pesquisar: "))
    for contacto in lista_contactos:
        if contacto["categoria"] == categoria:
            print(f"Nome: {contacto['nome']}")
            print(f"Idade: {contacto['idade']}")
            print(f"Telefone: {contacto['telefone']}")
            print(f"E-Mail: {contacto['email']}")
            categorias = {1: "Família", 2: "Amigos", 3: "Trabalho"}
            print(f"Categoria: {categorias[contacto['categoria']]}")
            break
        else:
            print("\nContacto não encontrado!")
    input("\nPressione Enter para voltar ao menu...")
    return menu()


def estatistica(lista_contactos):
    pass


def frase_automatica(lista_contactos):
    pass


menu()
