class RH:
    def __init__(self):
        self.funcionarios = []

    def adicionar_funcionario(self, func):
        self.funcionarios.append(func)

    def remover_funcionario(self, func):
        self.funcionarios.remove(func)

    def listar_funcionarios(self):
        lista = []
        for func in self.funcionarios:
            lista.append(func.nome)
        return lista

    def emitir_recibo(self, func):
        with open(f"Recibos - {func.numero} - {func.nome}", "a", encoding="utf-8") as recibo:
            recibo.write(
                "====================================================\n")
            recibo.write(f"Nº funcionário: {func.numero}\n")
            recibo.write(f"Nome: {func.nome}\n")
            if type(func) == "FuncionarioEfetivo":
                recibo.write(f"Salário base: {func.salario_base}\n")
            elif type(func) == "FuncionarioTempoParcial":
                recibo.write(f"Ganho por hora: {func.valor_hora}\n")
                recibo.write(f"Horas trabalhadas: {func.horas_trabalhadas}\n")
            recibo.write(
                f"Salário líquido: {func.calcular_salario_liquido()}\n")
            recibo.write(
                f"Dias de férias por gozar: {func.ferias.dias_disponiveis()}\n")

    def mostrar_estatisticas(self):
        print(len(self.funcionarios))
        total_salario = 0
        for func in self.funcionarios:
            total_salario += func.calcular_salario_liquido()
        print(f"{total_salario}€")


###########################################################################################


class Funcionario:
    def __init__(self, nome, numero, estado_civil, salario_base, categoria, contrato, assiduidade, ferias):
        self.nome = nome
        self.numero = numero
        self.estado_civil = estado_civil
        self.salario_base = salario_base
        self.categoria = categoria
        self.contrato = contrato
        self.assiduidade = assiduidade
        self.ferias = ferias

    def apresentar_dados(self):
        print(f"Nome: {self.nome}")
        print(f"Número: {self.numero}")
        print(f"Estado Civil: {self.estado_civil}")
        print(f"Salário Base: {self.salario_base}€")
        print(f"Categoria: {self.categoria}")
        print(f"Tipo de Contrato: {self.contrato.tipo}")
        print(f"Dias Totais de Férias: {self.ferias.dias_totais}")
        print(f"Dias Usados de Férias: {self.ferias.dias_usados}")

    def calcular_salario_liquido(self):
        return self.salario_base - (self.salario_base * 0.11) - (self.salario_base * 0.27)


###########################################################################################


class FuncionarioEfetivo(Funcionario):
    def __init__(self, nome, numero, estado_civil, salario_base, categoria, contrato, assiduidade, ferias):
        super().__init__(nome, numero, estado_civil, salario_base,
                         categoria, contrato, assiduidade, ferias)
        self.subsidio_alimentacao = 132

    def calcular_salario_liquido(self):
        total = self.salario_base + self.subsidio_alimentacao
        return total - (total * 0.11) - (total * 0.27)


###########################################################################################


class FuncionarioEstagiario(Funcionario):
    def __init__(self, nome, numero, estado_civil, categoria, contrato, assiduidade, ferias):
        self.nome = nome
        self.numero = numero
        self.estado_civil = estado_civil
        self.salario_base = 920
        self.categoria = categoria
        self.contrato = contrato
        self.assiduidade = assiduidade
        self.ferias = ferias

    def calcular_salario_liquido(self):
        return super().calcular_salario_liquido()


###########################################################################################


class FuncionarioTempoParcial(Funcionario):
    def __init__(self, nome, numero, estado_civil, categoria, contrato, assiduidade, ferias, horas_trabalhadas):
        self.nome = nome
        self.numero = numero
        self.estado_civil = estado_civil
        self.categoria = categoria
        self.contrato = contrato
        self.assiduidade = assiduidade
        self.ferias = ferias
        self.valor_hora = 25
        self.horas_trabalhadas = horas_trabalhadas

    def calcular_salario_liquido(self):
        total_trabalhado = self.valor_hora * self.horas_trabalhadas
        return total_trabalhado - (total_trabalhado * 0.11) - (total_trabalhado * 0.27)


###########################################################################################


class Contrato:
    def __init__(self, tipo, data_inicio):
        self.tipo = tipo
        self.data_inicio = data_inicio


###########################################################################################


class Ferias:
    def __init__(self, dias_totais, dias_usados):
        self.dias_totais = dias_totais
        self.dias_usados = dias_usados

    def dias_disponiveis(self):
        return self.dias_totais - self.dias_usados


###########################################################################################


class RegistoAssiduidade:
    def __init__(self, faltas, atrasos, horas_extra):
        self.faltas = faltas
        self.atrasos = atrasos
        self.horas_extra = horas_extra
