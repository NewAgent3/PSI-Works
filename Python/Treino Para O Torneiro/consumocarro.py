while True:
    k = int(input())
    l = float(input())
    if (k >= 0 or k <= 10000) == True and (l > 0 or l <= 100) == True:
        break
print(round(l/k * 100, 2))
