import datetime as dt
data = input("Diga uma data (Dia/Mês/Ano): ")
data = dt.datetime.strptime(data, "%d/%m/%Y")
print(data.date())
