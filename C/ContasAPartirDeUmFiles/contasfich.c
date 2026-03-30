#include <stdio.h>
#include <stdlib.h>

int main()
{
	int numa, numb, contar;
	char sinal;
	FILE *contas;
	system("chcp 65001");
	system("cls");
	contas = fopen("contas.txt", "r");
	for(contar = 0; contar < 6; contar++) {
		fscanf(contas, "%d %c %d", &numa, &sinal, &numb);
		switch(sinal) {
			case '+': {
				printf("%d %c %d = %d\n", numa, sinal, numb, numa + numb);
				break; }
			case '-': {
				printf("%d %c %d = %d\n", numa, sinal, numb, numa - numb);
				break; }
			case '/': {
				printf("%d %c %d = %d\n", numa, sinal, numb, numa / numb);
				break; }
			case '*': {
				printf("%d %c %d = %d\n", numa, sinal, numb, numa * numb);
				break; } } }
	fclose(contas);
	return 0;
}
