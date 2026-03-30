#include <stdio.h>
#include <stdlib.h>

int main()
{
	system("chcp 65001");
	system("cls");
	int linhas;
	char linha[100], nomeficheiro[100];
	FILE *historia;
	printf("Diga o nome do ficheiro que quer abrir (Incluir a extensão do ficheiro é obrigatório!):\n");
	scanf("%s", nomeficheiro);
	historia = fopen(nomeficheiro, "r");
	printf("Diga quantas linhas deseja ver?\n");
	scanf("%d", &linhas);
	for(int contar = 0; contar < linhas; contar++) {
		fgets(linha, 100, historia);
		printf("%s", linha); }
	return 0;
}

