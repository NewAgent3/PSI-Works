import random
from rich.progress import track
from rich.console import Console
import time
lista = ("lindo/a", "belo/a", "feio/a",
         "horrivel", "mal-cheiroso/a", "preto/a", "do Monte")
terminal = Console()
terminal.clear()
nome = terminal.input("Diga o seu nome, [underline]por favor[/underline]: ")
for _ in track(range(100), description="A verificar beleza..."):
    time.sleep(0.1)
terminal.print(f"O/A {nome} é {lista[random.randrange(0, len(lista))]}!!!")
