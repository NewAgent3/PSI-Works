#include <stdio.h>
#include <conio.h>
#include <stdlib.h>

int main()
{
	int in;
	float x, y;
	system("chcp 65001");
	numeros: {
		system("cls");
		printf("Escolha dois números:\n");
		scanf("%f%f", &x, &y);
		goto menu; }
	menu: {
		system("cls");
		printf("1 - Soma\n2 - Subtração\n3 - Divisão\n4 - Multiplição\n5 - Repor os números\n6 - Sair");
		printf("\n\nEscolha: ");
		scanf("%d", &in);
		switch(in) {
			case 1: {
				printf("\n\nResultado: %f", x + y);
				getchar();
				getchar();
				goto menu; }
			case 2: {
				printf("\n\nResultado: %f", x - y);
				getchar();
				getchar();
				goto menu; }
			case 3: {
				printf("\n\nResultado: %f", x / y);
				getchar();
				getchar();
				goto menu; }
			case 4: {
				printf("\n\nResultado: %f", x * y);
				getchar();
				getchar();
				goto menu; }
			case 5: {
				goto numeros; }
			case 6: {
				return 0;}
			default: {
				goto menu; } } }
}

