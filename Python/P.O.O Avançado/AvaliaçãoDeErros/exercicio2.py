while True:
    try:
        num = int(input("Numero Inteiro: "))
    except BaseException:
        pass
    else:
        print(num)
        quit()
