import pandas as pd

df = pd.read_excel('Automacao-teste.xlsx')

def consumir_planilha():
    dados = []

    for _, linha in df.iterrows():
        dados.append({
            "produto": linha["PRODUTO"],
            "valor": linha["VALOR"],
            "cupom": linha["CUPOM"],
            "link": linha["LINK"]
        })

    return dados    
