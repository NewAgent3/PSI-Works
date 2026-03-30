A = 9
B = 4
C = 5
# A:
if A <= 2 and B == 7:
    print("Verdadeiro")
else:
    print("Falso")
# B:
if not A == 2 and B == 7:
    print("Verdadeiro")
else:
    print("Falso")
# C:
if not (A == 3 and B == 7):
    print("Verdadeiro")
else:
    print("Falso")
# D:
if A < 5 and B > 2 or B != 7:
    print("Verdadeiro")
else:
    print("Falso")
# E:
if A == 3 and not B <= 4 and C == 8:
    print("Verdadeiro")
else:
    print("Falso")
