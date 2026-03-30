#include <stdio.h>
#include <stdlib.h>

int main()
{
	system("chcp 65001");
	system("cls");
	int jogador;
	char linha[100];
	FILE *euro;
	euro = fopen("euro.txt", "r");
	printf("Quantos jogadores quer ver?\n");
	scanf("%d", &jogador);
	system("cls");
	for(int contar = 0; contar < jogador; contar++) {
		fgets(linha, 100, euro);
		printf("%s", linha); }
	fclose(euro);
	return 0;
}
