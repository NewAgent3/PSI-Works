#include <stdio.h>
#include <stdlib.h>

int main()
{
	system("chcp 65001");
	system("cls");
	FILE *ocorrencia;
	char carater, nomefich[100], verify;
	int caratervezes = 0;
	printf("Diga o nome do ficheiro que deseja abrir (Incluindo a extensão do mesmo): ");
	scanf("%s", nomefich);
	ocorrencia = fopen(nomefich, "r");
	if(ocorrencia != NULL) {
		printf("\nDiga o carater que deseja procurar no ficheiro: ");
		scanf("%c", &carater);
		carater = getchar();
		while(!feof(ocorrencia)) {
			verify = getc(ocorrencia);
			if(carater == verify) {
				caratervezes++; } }
		if(caratervezes > 1) {
			printf("\nResultado: %d ocorrências do carater %c (Pressione Enter para sair)", caratervezes, carater);
			fclose(ocorrencia);
			getchar();
			getchar();
			return 0; }
		else {
			printf("\nResultado: %d ocorrência do carater %c (Pressione Enter para sair)", caratervezes, carater); 
			fclose(ocorrencia);
			getchar();
			getchar();
			return 0; } }
	else {
		printf("\nO FICHEIRO NÃO EXISTE!!!");
		fclose(ocorrencia);
		getchar();
		getchar();
		return 0; }
}

