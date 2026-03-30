#include <stdio.h>
#include <stdlib.h>

int main()
{
	int polegadas, milimetros;
	FILE *polemetros;
	printf("Diga as polegadas: ");
	scanf("%d", &polegadas);
	polemetros = fopen("./Milimetros.txt" ,"a");
	milimetros = polegadas * 25;
	fprintf(polemetros, "%d polegadas são %d mm\n", polegadas, milimetros);
	fclose(polemetros);
	return 0;
}

