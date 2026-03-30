import datetime as dt
ano = int(input("Diga o seu próximo aniversário (Ano): "))
mes = int(input("Diga o seu próximo aniversário (Mês): "))
dia = int(input("Diga o seu próximo aniversário (Dia): "))
print(dt.datetime(ano, mes, dia) - dt.datetime.now())
