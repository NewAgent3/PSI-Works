#include <stdio.h>
#include <stdlib.h>

int main()
{
	system("chcp 65001");
	system("cls");
	int jogador;
	char jogadores[100];
	FILE *salfut;
	salfut = fopen("futsal.txt", "r");
	menu: {
		rewind(salfut);
		system("cls");
		printf("//////////////// FUTSAL ////////////////\n");
		printf(" 1 - Mostrar os dados dos 10 jogadores\n");
		printf(" 2 - Procurar jogador pelo nº da camisola\n");
		printf(" 3 - Sair\n");
		printf("////////////////////////////////////////\n\n");
		printf("Input: ");
		scanf("%d", &jogador); }
	switch(jogador) {
		case 1: {
			printf("\n");
			for(int contar = 0; contar < 10; contar++) {
				fgets(jogadores, 100, salfut);
				printf("%s", jogadores); }
				getchar();
				getchar();
				goto menu; }
		case 2: {
			printf("\nDiga o número da camisola do jogador: ");
			scanf("%d", &jogador);
			for(int contar = 0; contar < jogador; contar++) {
				fgets(jogadores, 100, salfut); }
			printf("\n%s", jogadores); 
				getchar();
				getchar();
				goto menu; }
		case 3: {
			return 0; }
		default: {
			goto menu; } }
}

