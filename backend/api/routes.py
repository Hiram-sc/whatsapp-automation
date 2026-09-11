from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.whatsapp import abrir_whatsapp, enviar_mensagem
from backend.consumer import consumir_planilha  

router = APIRouter()

@router.get("/")
def painel():
    return FileResponse("front/index.html")

@router.get("/token")
def whatsapp():

    dados = consumir_planilha()

    pagina = abrir_whatsapp()

    for item in dados:
        mensagem = (
            f"{item['produto']}\n\n"
            f"💰 {item['valor']}\n"
            f"🏷️ {item['cupom']}\n"
            f"🔗 {item["link"]}"
        )

    enviar_mensagem(pagina, mensagem)

    return {"status": "mensagens enviadas"}