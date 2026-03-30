#include <stdio.h>

int main()
{
	int x, contar;
	printf("Escolhe um numero: ");
	scanf("%d", &x);
	contar = 1;
	while(contar <= 10) {
		printf("\n%d * %d = %d", x, contar, x * contar);
		contar++; }
	getchar();
	getchar();
	return 0;
}
