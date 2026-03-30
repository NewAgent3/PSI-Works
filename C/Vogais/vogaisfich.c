#include <stdio.h>
#include <stdlib.h>

int main()
{
	system("chcp 65001");
	system("cls");
	FILE *ocorrencia;
	char nomefich[100], verify;
	int caratervezes = 0;
	printf("Diga o nome do ficheiro que deseja abrir (Incluindo a extensão do mesmo): ");
	scanf("%s", nomefich);
	ocorrencia = fopen(nomefich, "r");
	if(ocorrencia != NULL) {
		while(!feof(ocorrencia)) {
			verify = getc(ocorrencia);
			if(verify == 'a' || 'A' || 'e' || 'E' || 'i' || 'I' || 'o' || 'O' || 'u' || 'U') {
				caratervezes++; } }
		if(caratervezes > 1) {
			printf("\nResultado: O ficheiro tem %d vogais (Pressione Enter para sair)", caratervezes);
			fclose(ocorrencia);
			getchar();
			getchar();
			return 0; }
		else {
			printf("\nResultado: O ficheiro tem %d vogal (Pressione Enter para sair)", caratervezes); 
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

