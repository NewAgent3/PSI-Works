#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int main()
{
	system("chcp 65001");
	system("cls");
	char linha[100], jogador [100];
	FILE *euro;
	euro = fopen("euro.txt", "a+");
	printf("         Jogadores\n----------------------------\n");
	while(fgets(linha, 100, euro)) {
		printf("%s", linha); }
	printf("\n\nInsira o nome de um jogador:\n");
	gets(jogador);
	fprintf(euro, "\n%s", jogador);
	system("cls");
	rewind(euro);
	while(fgets(linha, 100, euro)) {
		printf("%s", linha); }
	fclose(euro);
	return 0;
}
