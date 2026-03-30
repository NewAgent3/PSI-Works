class ContaBancaria:
    def __init__(self, nome, saldo):
        self.nome = nome
        self.saldo = saldo

    def depositar(self, valor):
        self.saldo = self.saldo + valor
        print(f"Inseriu {valor}€ na conta de {self.nome}!")

    def consultar_saldo(self):
        print(f"Saldo de {self.nome}: {self.saldo}€")

    def levantar(self, valor):
        if valor > self.saldo:
            print(
                f"Não tem saldo suficiente! Tentou levantar {valor}€, mas apenas tem {self.saldo}€ na conta!")
        else:
            self.saldo = self.saldo - valor
            print(f"Feito! Tem {self.saldo}€ na conta!")


conta1 = ContaBancaria("Abel", 100)
print("BANCO DO TITIO BONSOIR\n")
print(
    f"CONTA 1:\nBom dia, {conta1.nome}! Tem {conta1.saldo}€ na conta!\n")
conta1.depositar(200)
conta1.consultar_saldo()
conta1.levantar(500)
conta1.levantar(20)
conta1.consultar_saldo()
print("\nCONTA 2:")
nome_conta2 = input(
    "Obrigada por criar uma conta no banco do Titio Bonsoir! Qual é o seu nome: ")
conta2 = ContaBancaria(nome_conta2, 0)
conta2.levantar(100)
valor = int(input("Quanto é que quer depositar: "))
conta2.depositar(valor)
conta2.consultar_saldo()
