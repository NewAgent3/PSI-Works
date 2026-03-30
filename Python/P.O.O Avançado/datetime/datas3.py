import datetime as dt
data = input("Data de Nascimento (Ano-Mês-Dia): ")
try:
    data = dt.datetime.strptime(data, "%Y-%m-%d")
except ValueError:
    print("Burro, não é assim negro de merda")
else:
    idade = dt.datetime.today().date().year - data.year
    if data.month > dt.datetime.today().date().month:
        idade -= 1
    elif data.month == data.month > dt.datetime.today().date().month and data.day > dt.datetime.today().date().day:
        idade -= 1
    print(idade)
