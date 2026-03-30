#include <stdio.h>
#include <stdlib.h>

int main()
{
	int numero;
	system("chcp 65001");
	system("cls");
	printf("Escreve um número: ");
	scanf("%d", &numero);
	for(int contar = numero; contar >= 0; contar--) {
		if(contar % 2 == 1) {
				printf("\n%d", contar); } }
	return 0;
}

