class Aluno:
    def __init__(self, nome, idade, curso):
        self.nome = nome
        self.idade = idade
        self.curso = curso
        self.notas = []

    def mostrar_informacoes(self):
        print(f"\nNome: {self.nome}")
        print(f"Idade: {self.idade}")
        print(f"Curso: {self.curso}")
        print(f"Notas: {self.notas}")

    def adicionar_nota(self, nova_nota):
        self.notas.append(nova_nota)

    def calcular_media(self):
        if len(self.notas) == 0:
            return False
        else:
            return (sum(self.notas) / len(self.notas))

    def mostrar_melhor_nota(self):
        if len(self.notas) == 0:
            return False
        else:
            return max(self.notas)

    def mostrar_aprovado(self):
        if len(self.notas) == 0:
            return False
        else:
            if (sum(self.notas) / len(self.notas)) >= 9.5:
                return True
            else:
                return False

    def atualizar_idade(self, nova_idade):
        self.idade = nova_idade

    def contar_notas(self):
        if len(self.notas) == 0:
            return False
        else:
            return len(self.notas)

    def mostrar_estado_academico(self):
        if len(self.notas) == 0:
            return False
        else:
            if (sum(self.notas) / len(self.notas)) >= 17:
                return "Excelente"
            elif (sum(self.notas) / len(self.notas)) >= 14:
                return "Bom"
            elif (sum(self.notas) / len(self.notas)) >= 9.5:
                return "Suficiente"
            else:
                return "Reprovado"
