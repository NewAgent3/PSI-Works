frase = input("Diga uma frase: ")
print("\n1 - Contagem de palavras")
print("2 - Converter para Maiúsculas e Minúsculas")
print("3 - Verificar de tem a palavra 'Python'")
print("4 - Inverter a frase")
print("5 - Substituir uma parte da frase por outra")
print("6 - Remover espaços extra")
print("7 - Verificar quantas vezes uma palavra aparece")
print("8 - Verificar se a frase é um palíndromo")
print("9 - Dar uma frase e receber ela dividida com vírgulas")
print("10 - Transformar todas as primeiras letras para maiúsculo")
print("11 - Encontrar a primeira vez que uma frase aparece\n")
opcao = int(input("\nOpção: "))
match opcao:
    case 1:
        print(f"\nNúmero de palavras: {len(frase.split())}")
    case 2:
        print(f"\nMaiúsculo: {frase.upper()}")
        print(f"Minúsculo: {frase.lower()}")
    case 3:
        if "Python" or "python" in frase == True:
            print("\nA palavra Python foi encontrada na frase!")
        else:
            print("\nA palavra Python não foi encontrada na frase!")
    case 4:
        print(f"\nFrase invertida: {frase[::-1]}")
    case 5:
        frase_palavra_parte = input("\nDiga uma frase/palavra: ")
        frase_antiga = input("Diga a parte antiga da frase: ")
        print(
            f"A frase agora é '{frase.replace(frase_antiga, frase_palavra_parte)}'")
    case 6:
        frase_formatada = frase.split()
        print(f"\n{" ".join(frase_formatada)}")
    case 7:
        palavra = input("\nDiga uma palavra: ").lower()
        frase_lista = frase.lower().split()
        print(
            f"\nA palavra {palavra.capitalize()} aparece na frase {frase_lista.count(palavra)} vezes")
    case 8:
        if frase.lower().replace(" ", "") == frase.lower().replace(" ", "")[::-1]:
            print("A frase é um palíndromo!")
        else:
            print("A frase não é um palíndromo!")
    case 9:
        frase_lista = frase.split()
        print(f"\n{",".join(frase_lista)}")
    case 10:
        print(f"\n{frase.title()}")
    case 11:
        palavra = input("\nDiga uma palavra: ")
        if frase.find(palavra) > -1:
            print(f"\nA palavra {palavra} foi encontrada na frase!")
        else:
            print(f"\nA palavra {palavra} não foi encontrada na frase!")
