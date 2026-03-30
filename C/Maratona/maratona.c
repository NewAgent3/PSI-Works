#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main()
{
	system("chcp 65001");
	system("cls");
	char nome[100], pais[100], tempo[100], linha[200], dump2[200], inc[200];
	int in, dump;
	FILE *tonamara;
	tonamara = fopen("maratona.txt", "r+");
	if(tonamara != NULL) {
	    menu: {
		rewind(tonamara);
		system("cls");
		printf("---------------------------- MARATONA OLÍMPICA (LA 2028) ----------------------------\n");
		printf("                    1 - Acrescentar dados sobre um novo campeão\n");
		printf("                    2 - Procurar atleta pelo ano em que venceu\n");
		printf("                    3 - Procurar atleta pelo país\n");
		printf("                    4 - Listar os dados de todos os campeões\n");
		printf("                    5 - Apagar o ficheiro\n");
		printf("                    0 - Sair\n");
		printf("-------------------------------------------------------------------------------------\n\n");
		printf("Input: ");
		scanf("%d", &in); }
		switch(in) {
			case 1: {
				while(fgets(linha, 200, tonamara)) {
					if(feof(tonamara)) {
						break; } }
				fprintf(tonamara, "2028 \tLos_Angeles \t");
				printf("Qual é o nome do campeão (Utilizar underscore em vez de espaço): ");
				scanf("%s", nome);
				fprintf(tonamara, "%s \t", nome);
				printf("\nQual é o país de nascença do campeão (Utilizar underscore em vez de espaço): ");
				scanf("%s", pais);
				fprintf(tonamara, "%s \t", pais);
				printf("\nQual foi o tempo final do campeão (Utilizar underscore em vez de espaço): ");
				scanf("%s", tempo);
				fprintf(tonamara, "%s\n", tempo);
				printf("\n\nCampeão %s de %s foi adicionado ao ficheiro! Pressione Enter para voltar ao menu principal\n", nome, pais);
				getchar();
				getchar();
				goto menu;  }
			case 2: {
				fgets(dump2, 200, tonamara);
				system("cls");
				printf("Qual é o ano das Maratonas Olímpicas que quer ver?\n\n");
				printf("Input: ");
				scanf("%d", &in);
				while(1 == 1) {
					fscanf(tonamara, "%d \t%s \t%s \t%s \t%s\n", &dump, dump2, nome, pais, tempo);
					printf("%d %s %s %s %s\n", dump, dump2, nome, pais, tempo);
					if(dump == in) {
						break; } }
				printf("O campeão da Maratona de %d %s foi o %s, que é de %s e teve um tempo de %s! Pressione Enter para voltar ao menu principal\n", in, dump2, nome, pais, tempo);
				getchar();
				getchar();
				goto menu; }
			case 3: {
				fgets(dump2, 200, tonamara);
				system("cls");
				printf("Qual é o país que ganhou as Maratonas Olímpicas que quer ver?\n\n");
				printf("Input: ");
				scanf("%s", inc); 
				while(!feof(tonamara)) {
					fscanf(tonamara, "%d \t%s \t%s \t%s \t%s\n", &dump, dump2, nome, pais, tempo);
					if(strcmp(inc, pais) == 0) {
						printf("O campeão da Maratona de %d %s foi o %s, que é de %s e teve um tempo de %s!\n", dump, dump2, nome, pais, tempo); } }
				printf("\n\nPressione Enter para voltar ao menu principal...");
				getchar();
				getchar();
				goto menu; }
			case 4: {
				system("cls");
				while(fgets(linha, 200, tonamara)) {	
					printf("%s", linha); }
				printf("\nPressione Enter para voltar ao menu principal...");
				getchar();
				getchar();
				goto menu; }
			case 5: {
				printf("\nTEM A CERTEZA? ISTO VAI APAGAR TUDO OQUE ESTIVER DENTRO DO FICHEIRO!!!\n");
				printf("\n0 - Sim\n1 - Não\n\n");
				printf("Input: ");
				scanf("%d", &in);
				switch(in) {
					case 0: {
						fclose(tonamara);
						system("del maratona.txt");
						printf("\nFicheiro foi apagado com sucesso, pressione Enter para fechar o programa\n");
						getchar();
						getchar();
						return 0; }
					case 1: {
						printf("O ficheiro não vai ser apagado e você será redirecionado para o menu principal, pressione Enter para voltar\n");
						getchar();
						getchar();
						goto menu; } } }
			case 0: {
				fclose(tonamara);
				return 0; }
			default: {
				goto menu; } } }
	else {
		printf("O FICHEIRO NÃO EXISTE!!! Pressione Enter para sair\n");
		fclose(tonamara);
		getchar();
		return 0; }
}
