#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main()
{
	system("chcp 65001");
	system("cls");
	FILE *dados;
	char turma, filename[40];
	system("mkdir Escola");
	printf("Diga a sua turma: ");
	scanf("%c", &turma);
	printf("Nome do ficheiro: ");
	scanf("%s", filename);
	dados = fopen(strcat(filename, ".txt"), "w");
	fprintf(dados, "Parabéns por seres aluno da ESCT\n");
	fprintf(dados, "O aluno é da turma %c\n", turma);
	fclose(dados);
	return 0;
}

