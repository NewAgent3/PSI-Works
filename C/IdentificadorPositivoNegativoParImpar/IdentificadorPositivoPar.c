#include <stdio.h>
#include <stdlib.h>

int main()
{
	int num;
	FILE *numero;
	system("chcp 65001");
	system("cls");
	printf("Escreve um número: ");
	scanf("%d", &num);
	numero = fopen("./numero.txt", "a");
	if(num % 2 == 0) {
		fprintf(numero,"%d - Par e ", num); }
	else {
		fprintf(numero,"%d - Impar e ", num); }
	if(num > 0) {
		fprintf(numero,"positivo\n"); }
	else {
		fprintf(numero,"negativo\n"); }
	fclose(numero);
	return 0;
}

