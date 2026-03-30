#include <stdio.h>
#include <stdlib.h>

int main()
{
	system("chcp 65001");
	system("cls");
	int numero;
	FILE *tabuada;
	tabuada = fopen("tabuada.txt", "w");
	printf("Digite um número: ");
	scanf("%d", &numero);
	for(int contar = 0; contar < 10; contar++) {
		fprintf(tabuada, "%d X %d = %d\n", numero, contar + 1, numero * (contar + 1)); }
	fclose(tabuada);
}
