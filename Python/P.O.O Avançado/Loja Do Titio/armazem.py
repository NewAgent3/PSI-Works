from funcionario import Funcionario


class Armazem(Funcionario):
    def __init__(self, nome, morada, telefone, data_nascimento, salario_base):
        super().__init__(nome, morada, telefone, data_nascimento, salario_base)
        self.cartao_ativo = False
        self.estado_entrada = False

    def entrada(self):
        self.estado_entrada = True

    def saida(self):
        self.estado_entrada = False

    def alterar_acesso(self):
        if self.cartao_ativo == False:
            self.cartao_ativo = True
        else:
            self.cartao_ativo = False
