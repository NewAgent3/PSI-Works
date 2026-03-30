#include <stdio.h>
#include <stdlib.h>

int main()
{
	int media, nota, contar;
	char nome[50];
	FILE *notas;
	system("chcp 65001");
	system("cls");
	media = 0;
	notas = fopen("notas.txt", "r");
	printf("-------- MÉDIA DAS NOTAS --------\n");
	for(contar = 0; contar < 5; contar++) {
		fscanf(notas,"%s %d", nome, &nota);
		media = media + nota; }
	printf("\t%d", media / 5);
	fclose(notas);
	return 0;
}
