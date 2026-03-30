import colorama as cr
from colorama import Fore, Back, Style
largura = int(input("Qual é a largura que quer no seu cartão: "))
nome = input("Digite o seu nome: ")
idade = int(input("Digite a sua idade: "))
trabalho = input("Digite a sua profissão: ")
print(Fore.RED, "=" * largura, Fore.RESET)
print(Back.BLUE, f"{'CARTÃO DE APRESENTAÇÃO':^{largura - 1}}", Back.RESET)
print(Fore.RED, "=" * largura)
print(Fore.GREEN, "Nome:", Fore.RESET, f"{nome:>{largura - 7}}")
print(Fore.GREEN, "Idade:", Fore.RESET, f"{idade:>{largura - 8}}")
print(Fore.GREEN, "Profissão:", Fore.RESET, f"{trabalho:>{largura - 12}}")
print(Fore.RED, "=" * largura, Fore.RESET)
print(Fore.GREEN, "Bem vindo(a),", Fore.MAGENTA,
      f"{nome:^{largura - 25}}", Style.RESET_ALL)
