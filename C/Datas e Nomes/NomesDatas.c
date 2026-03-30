#include <stdio.h>
#include <stdlib.h>

int main()
{
	int datas[5];
	char nomes[20][5];
	system("chcp 65001");
	system("cls");
	printf("Digite 5 anos de nascimento:\n");
	for(int contar = 0; contar <= 4; contar++) {
		scanf("%d", &datas[contar]); }
	printf("\nDigite 5 nomes de pessoas:\n");
	for(int contar = 0; contar <= 4; contar++) {
		scanf("%s", nomes[contar]); }
	system("cls");
	for(int contar = 0; contar <= 4; contar++) {
		printf("%s tem %d anos\n", nomes[contar], 2025 - datas[contar]); }
}
