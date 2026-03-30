#include <stdio.h>
#include <stdlib.h>

int main()
{
	int soma, nums[10], contar, maior, menor;
	float media;
	system("chcp 65001");
	system("cls");
	printf("Digite 10 notas (1 a 20):\n");
	soma = 0;
	maior = 1;
	menor = 20;
	for(contar = 0; contar <= 10; contar++) {
		scanf("%d", &nums[contar]);
		soma = soma + nums[contar];
		if(nums[contar] > maior) { 
			maior = nums[contar]; }
		if(nums[contar] < menor) { 
			menor = nums[contar]; } }
	media = soma / contar;
	printf("\nSoma de todas as notas: %d", soma);
	printf("\nMédia de todas as notas: %.2f", media);
	printf("\nA maior nota: %d", maior);
	printf("\nA menor nota: %d", menor);
	return 0;
}
