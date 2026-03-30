# Program to check if a number is prime or not
num = int(input("Enter a number: "))

resultado = 0

if num == 0 or num == 1:
    pass
elif num > 1:
    # check for factors
    for i in range(2, num):
        if (num % i) == 0:
            # if factor is found, set flag to True
            resultado = 1
            # break out of loop
            break

    # check if flag is True
    if resultado == 1:
        print(num, "is not a prime number")
    else:
        print(num, "is a prime number")
