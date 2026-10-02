import pandas as pd 

def consumir_planilha(caminho_arquivo):

    df = pd.read_excel(caminho_arquivo)
    
    dados = []

    for _, linha in df.iterrows():
        dados.append({
            "produto": linha["PRODUTO"],
            "valor": linha["VALOR"],
            "cupom": linha["CUPOM"],
            "link": linha["LINK"]
        })

    return dados