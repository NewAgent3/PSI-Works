#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main()
{
	system("chcp 65001");
	system("cls");
	int num, contribuinte, contador = 0, media;
	char cliente[100][2], dump[100], linha2[100], linha[100], linha3[100];
	FILE *digi;
	digi = fopen("digi.txt", "a+");
	menu: {
		system("cls");
		rewind(digi);
		printf("------------------------ DIGI ------------------------\n");
		printf("      1 - Inserir cliente\n");
		printf("      2 - Mostrar a média das idades dos clientes\n");
		printf("      3 - Listar os dados de todos os clientes\n");
		printf("      4 - Procurar cliente pelo seu nº contribuinte\n");
		printf("      0 - Sair\n");
		printf("------------------------------------------------------\n\n");
		printf("Input: "); }
	scanf("%d", &num);
	switch(num) {
		case 1: {
			system("cls");
			printf("Diga o seu número de contribuinte: ");
			scanf("%d", &contribuinte);
			fprintf(digi, "%d ", contribuinte);
			printf("Diga o seu nome: ");
			gets(cliente[0]);
			fprintf(digi, "%s ", cliente[0]);
			printf("Diga a sua localidade: ");
			gets(cliente[1]);
			fprintf(digi, "%s ", cliente[1]);
			printf("Diga o seu código postal: ");
			gets(cliente[2]);
			fprintf(digi, "%s ", cliente[2]);
			printf("Diga a sua idade: ");
			scanf("%d", &num);
			fprintf(digi, "%d\n", num);			
			goto menu; } 
		case 2: {
			media = 0;
			contador = 0;
			while(1 == 1) {
				fscanf(digi, "%d %s %s %s %d", &contribuinte, cliente[0], cliente[1], cliente[2], &num);
				if(!feof(digi)) {
					media = media + num ;
					contador++; }
				else {
					break; } }
			printf("\nA média das idades dos clientes DIGI é %d\n", media / contador); 
			getchar();
			getchar();
			goto menu; }
		case 3: {
			system("cls");
			while(fgets(dump, 100, digi)) {
				printf("%s", dump); } 
			getchar();
			getchar();
			goto menu; }
		case 4: {
			system("cls");
			printf("Diga o seu contribuinte: ");
			scanf("%d", &contador);
			while(1 == 1) {
				fscanf(digi, "%d %s %s %s %d", &contribuinte, linha, linha2, linha3, &num);
				if(contribuinte == contador) {
					printf("%d %s %s %s %d", contribuinte, linha, linha2, linha3, num);
					break; } }
			getchar();
			getchar();
			goto menu; }
		case 0: {
			fclose(digi);
			return 0; }
		default: {
			goto menu; } }
}
