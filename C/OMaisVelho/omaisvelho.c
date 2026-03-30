#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int main()
{
	int idades[3], idademaior = INT_MIN, posidade=0, posnome=0;
	char nomes[3][50];
	FILE *velho;
	system("chcp 65001");
	system("cls");
	velho = fopen("O Mais Velho.txt", "w");
	printf("Diga os nomes 3 pessoas: \n");
	for(int contar = 0; contar < 3; contar++) {
		scanf("%s", nomes[contar]); }
	printf("\nDiga as idades das 3 pessoas: \n");
	for(int contar = 0; contar < 3; contar++) {
		scanf("%d", &idades[contar]); }
	for(int contar2 = 0; contar2 < 3; contar2++) {
		if(idades[contar2] > idademaior ) {
			idademaior = idades[contar2];
			posidade = contar2;
			posnome = contar2; } }
	fprintf(velho, "%s - %d anos\n", nomes[posnome], idades[posidade]);
	return 0;
}
