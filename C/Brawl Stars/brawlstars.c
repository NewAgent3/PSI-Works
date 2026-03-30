#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

int main()
{
	system("chcp 65001");
	system("cls");
	char nome[100], brawler[100], linha[200], dump2[200];
	int in, nivel, trofeus, maior = INT_MIN;
	FILE *bsj;
	bsj = fopen("bslistajogadores.txt", "a+");
	if(bsj != NULL) {
	    menu: {
		rewind(bsj);
		system("cls");
		printf("---------------------------- BRAWL STARS STATS ----------------------------\n");
		printf("                 1 - Adicionar novo jogador\n");
		printf("                 2 - Mostrar todos os jogadores\n");
		printf("                 3 - Procurar jogador pelo nome\n");
		printf("                 4 - Mostrar o jogador com mais troféus\n");
		printf("                 0 - Sair\n");
		printf("---------------------------------------------------------------------------\n\n");
		printf("Input: ");
		scanf("%d", &in); }
		switch(in) {
			case 1: {
				system("cls");
				printf("Qual é o seu nome de utilizador? (Não utilizar espaços): ");
				scanf("%s", nome);
				fprintf(bsj, "%s ", nome);
				printf("\nQual é o seu nível? (Não utilizar espaços): ");
				scanf("%d", &nivel);
				fprintf(bsj, "%d ", nivel);
				printf("\nQuantos troféus tem? (Não utilizar espaços): ");
				scanf("%d", &trofeus);
				fprintf(bsj, "%d ", trofeus);
				printf("\nQual é o seu brawler favorito? (Utilizar underscore em vez de espaço): ");
				scanf("%s", brawler);
				fprintf(bsj, "%s\n", brawler);
				printf("\n\nJogador criado e adicionado á lista! Pressione Enter para voltar ao menu principal\n");
				getchar();
				getchar();
				goto menu;  }
			case 2: {
				system("cls");
				while(fgets(linha, 200, bsj)) {
					printf("%s\n", linha); }
				printf("\n\nPressione Enter para voltar ao menu principal...\n");
				getchar();
				getchar();
				goto menu; }
			case 3: {
				system("cls");
				printf("Qual é o nome do jogador? (Não utilizar espaços): ");
				scanf("%s", dump2);
				while(fscanf(bsj, "%s %d %d %s", nome, &nivel, &trofeus, brawler)) {
					if(strcmp(dump2, nome) == 0) {
						printf("%s %d %d %s\n", nome, nivel, trofeus, brawler);
						break; } }
				printf("\n\nPressione Enter para voltar ao menu principal...\n"); 
				getchar();
				getchar();
				goto menu; }
			case 4:
				system("cls");
				maior = INT_MIN;
				while(fscanf(bsj, "%s %d %d %s", nome, &nivel, &trofeus, brawler)) {
					if(maior < trofeus) {
						maior = trofeus;
						strcpy(dump2, nome); }
					if(feof(bsj)) {
						break; } }
				printf("O jogador com mais troféus é %s, com um total de %d troféus!\n", dump2, maior);
				printf("\nPressione Enter para voltar ao menu principal...");
				getchar();
				getchar();
				goto menu;
			case 0: {
				fclose(bsj);
				return 0; }
			default: {
				goto menu; } } }
	else {
		printf("O FICHEIRO NÃO EXISTE!!! Pressione Enter para sair\n");
		fclose(bsj);
		getchar();
		return 0; }
}
