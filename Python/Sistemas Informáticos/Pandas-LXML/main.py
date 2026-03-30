import pandas as pd
url = "https://www.w3schools.com/html/html_tables.asp"
website = pd.read_html(url)
tabela = website[0]
print(tabela[tabela["Country"] == "Germany"])
tabela.to_excel("TitioCorp.xlsx", index=False)
print("\n")
print(pd.read_excel("TitioCorp.xlsx"))
