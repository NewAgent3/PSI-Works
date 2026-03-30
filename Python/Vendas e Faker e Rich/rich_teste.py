from rich.console import Console
from rich.progress import track
import time
terminal = Console()
terminal.log()
terminal.print(
    "Olá [bold][green]Mundo[/green][/bold] do [bold][yellow]Rich[bold]")
terminal.clear()
terminal.print("Eu sou :fire:")
nome = terminal.input("Diga o seu [underline bold]nome[/underline bold]: ")
for _ in track(range(100), description="A gerar mensagem..."):
    time.sleep(0.1)
terminal.print(f"O {nome.capitalize()} é :fire:")
