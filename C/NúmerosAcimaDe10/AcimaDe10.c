#include <stdio.h>
#include <stdlib.h>

int main()
{
	int contagem, soma, nums[15], contar;
	system("chcp 65001");
	system("cls");
	printf("Digite 15 números:\n");
	contagem = 0;
	soma = 0;
	for(contar = 0; contar <= 15; contar++) {
		scanf("%d", &nums[contar]);
		if(nums[contar] > 10) {
				contagem++;
				soma = soma + nums[contar]; } }
	printf("\nQuantidade de números maiores que 10: %d", contagem);
	printf("\nSoma de todos os números maiores que 10: %d", soma);
	return 0;
}

