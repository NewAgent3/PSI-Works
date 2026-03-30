import pandas as pd
pagina = pd.read_html(
    "https://www.pwc.pt/pt/pwcinforfisco/orcamentoestado/irs-e-seguranca-social.html", encoding='utf-8')
print(pagina[0])
