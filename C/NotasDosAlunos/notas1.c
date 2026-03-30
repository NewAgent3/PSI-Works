#include <stdio.h>
#include <stdlib.h>

int main()
{
	int nota, contar;
	char nomes[50];
	FILE *notas;
	system("chcp 65001");
	system("cls");
	notas = fopen("notas.txt", "r");
	printf("-------- NOTAS NEGATIVAS --------\n");
	for(contar = 0; contar < 5; contar++) {
		fscanf(notas,"%s %d", nomes, &nota);
		if(nota < 10) {
			printf("NOME: %s\tNOTA: %d\n", nomes, nota); } }
	rewind(notas);
	printf("-------- NOTAS POSITIVAS --------\n");
	for(contar = 0; contar < 5; contar++) {
		fscanf(notas,"%s %d", nomes, &nota);
		if(nota >= 10) {
			printf("NOME: %s\tNOTA: %d\n", nomes, nota); } }
	fclose(notas);
	return 0;
}
