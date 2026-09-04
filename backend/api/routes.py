from fastapi import APIRouter
from fastapi.responses import RedirectResponse, FileResponse

from backend.whatsapp import criar_mensagem
from backend.consumer import consumir_planilha  

router = APIRouter()

@router.get("/")
def painel():
    return FileResponse("front/index.html")

@router.get("/token")
def abrir_whatsapp():

    dados = consumir_planilha

    for item in dados():

        url = criar_mensagem(
            item["produto"],
            item["valor"],
            item["cupom"],
            item["link"]
        )

    return RedirectResponse(url=url)