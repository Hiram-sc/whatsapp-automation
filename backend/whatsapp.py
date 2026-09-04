from backend.consumer import consumir_planilha

from urllib.parse import quote
import time
import webbrowser


def criar_mensagem(produto, valor, cupom, link):

    mensagem = quote(
        f"  {produto} \n\n"
        f"💰 {valor} \n"
        f"🏷️ {cupom} \n"
        f"🔗 {link} \n"
    )

    url = (f"https://api.whatsapp.com/send?phone=5522998452260&text={mensagem}")

    return url

