from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.whatsapp import abrir_whatsapp, conversa, aguardar_gatilho, enviar_mensagem
from backend.consumer import consumir_planilha 

import time

router = APIRouter()

@router.get("/")
def painel():
    return FileResponse("front/index.html")

@router.get("/token")
def whatsapp():

    print("Consumindo planilha...")
    dados = consumir_planilha()

    pagina = abrir_whatsapp()
    print(f"Whatsapp aberto.")

    nome_conversa = conversa(pagina)
    print(f"Conversa Detectada: {nome_conversa}")

    aguardar_gatilho(pagina)
    print("Gatilho executado!")

    for item in dados:
        mensagem = (
            f"{item['produto']}\n\n"
            f"💰 {item['valor']}\n"
            f"🏷️ {item['cupom']}\n"
            f"🔗 {item["link"]}"
        )

        enviar_mensagem(pagina, mensagem)

        time.sleep(3)

    return {"status": "envios iniciados"}