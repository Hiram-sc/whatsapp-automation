from pathlib import Path

import pandas as pd


COLUNAS_OBRIGATORIAS = ("PRODUTO", "VALOR", "CUPOM", "LINK")
LIMITE_ERROS_EXIBIDOS = 10


def _texto(valor) -> str:
    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass

    return str(valor).strip()


def _normalizar_link(valor) -> str | None:
    link = _texto(valor)

    if not link:
        return None

    minusculo = link.lower()

    if minusculo.startswith(("http://", "https://")):
        return link

    if minusculo.startswith("www.") or minusculo.startswith("wa.me/"):
        return f"https://{link}"

    return None


def _converter_valor(valor) -> float | None:
    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(valor, bool):
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip().replace("R$", "").replace(" ", "")

    if not texto:
        return None

    try:
        return float(texto)
    except ValueError:
        pass

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return None


def consumir_planilha(caminho_arquivo: str | Path) -> list[dict]:
    caminho = Path(caminho_arquivo)

    if not caminho.is_file():
        raise ValueError("O arquivo da planilha não foi encontrado.")

    try:
        df = pd.read_excel(caminho, engine="openpyxl")
    except Exception as erro:
        raise ValueError(
            "Não foi possível ler a planilha. "
            "Envie um arquivo .xlsx válido."
        ) from erro

    df.columns = [str(coluna).strip().upper() for coluna in df.columns]

    colunas_ausentes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in df.columns
    ]

    if colunas_ausentes:
        raise ValueError(
            "A planilha não possui as colunas obrigatórias: "
            + ", ".join(colunas_ausentes)
            + "."
        )

    if df.empty:
        raise ValueError("A planilha não contém linhas para processar.")

    df = df.dropna(
        subset=list(COLUNAS_OBRIGATORIAS),
        how="all",
    )

    if df.empty:
        raise ValueError(
            "A planilha não contém linhas preenchidas para processar."
        )

    dados = []
    erros = []

    for posicao, (indice, linha) in enumerate(df.iterrows()):
        try:
            numero_linha = int(indice) + 2
        except (TypeError, ValueError):
            numero_linha = posicao + 2

        produto = _texto(linha["PRODUTO"])
        cupom = _texto(linha["CUPOM"])
        link_bruto = _texto(linha["LINK"])
        link = _normalizar_link(link_bruto)
        valor = _converter_valor(linha["VALOR"])

        if not produto:
            erros.append(f"linha {numero_linha}: PRODUTO vazio")

        if valor is None:
            erros.append(f"linha {numero_linha}: VALOR inválido")

        if not cupom:
            erros.append(f"linha {numero_linha}: CUPOM vazio")

        if not link_bruto:
            erros.append(f"linha {numero_linha}: LINK vazio")
        elif link is None:
            erros.append(
                f"linha {numero_linha}: LINK inválido; "
                "use http://, https://, www."
            )

        if produto and valor is not None and cupom and link:
            dados.append(
                {
                    "produto": produto,
                    "valor": valor,
                    "cupom": cupom,
                    "link": link,
                }
            )

    if erros:
        detalhes = "; ".join(erros[:LIMITE_ERROS_EXIBIDOS])

        if len(erros) > LIMITE_ERROS_EXIBIDOS:
            detalhes += f"; e mais {len(erros) - LIMITE_ERROS_EXIBIDOS} erro(s)"

        raise ValueError(f"Planilha inválida: {detalhes}.")

    if not dados:
        raise ValueError("A planilha não contém mensagens para enviar.")

    return dados
