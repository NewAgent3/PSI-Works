import colorama as cr
from colorama import Fore, Back, Style
produtos = ["Pão", "Leite"]
precos = [1.20, 0.95]
TAXA_IVA = (0.23)
print(Style.RESET_ALL, Back.MAGENTA, "=" * 7,
      "GESTÃO DE COMPRAS", "=" * 7, Back.RESET, "\n")
produto = input(" Nome do produto: ").capitalize()
preco = float(input(" Preço (€): "))
produtos.append(produto)
precos.append(preco)
print(Fore.LIGHTBLACK_EX, Style.BRIGHT,
      f"\n Produto '{produto}' adicionado com sucesso!\n", Fore.RESET, Style.RESET_ALL)
print(Fore.GREEN, "=" * 8, "RECIBO FINAL", "=" * 8, Fore.RESET)
print(Fore.BLUE, "Produto", f"{'Preço (€)':>22}")
print(Fore.RED, "-" * 30, Fore.RESET)
print(f" {produtos[0]:<0}", f"{precos[0]:>{29 - len(produtos[0])}.2f}")
print(f" {produtos[1]:<0}", f"{precos[1]:>{29 - len(produtos[1])}.2f}")
print(f" {produto:<0}",
      f"{precos[2]:>{29 - len(produtos[2])}.2f}")
print(Fore.RED, "-" * 30, Fore.RESET)
print(f"{' Subtotal:':<0}", f"{sum(precos):>20.2f}")
print(f"{' IVA (23%):':<0}", f"{sum(precos) * TAXA_IVA:>19.2f}")
print(f"{' TOTAL:':<0}",
      f"{sum(precos) + (sum(precos) * TAXA_IVA):>23.2f}")
print(Fore.GREEN, "=" * 30, Style.RESET_ALL)
