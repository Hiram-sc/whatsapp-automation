from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse

from pathlib import Path

from backend.whatsapp import abrir_whatsapp, conversa, aguardar_gatilho, enviar_mensagem
from backend.consumer import consumir_planilha 
from backend.status import zerar_contagem, registrar_envio, obter_contagem

import time
import shutil

router = APIRouter()

UPLOAD_DIR = Path("uploads") 
UPLOAD_DIR.mkdir(exist_ok=True) 

@router.get("/")
def painel():
    return FileResponse("front/index.html")

@router.post("/iniciar")
def whatsapp(
    planilha: UploadFile = File(...),
    intervalo: int = Form(...)
):

    caminho_arquivo = UPLOAD_DIR / planilha.filename

    with caminho_arquivo.open("wb") as arquivo:
        shutil.copyfileobj(planilha.file, arquivo)

    print("Consumindo planilha...")
    dados = consumir_planilha(caminho_arquivo)

    zerar_contagem()

    pagina = abrir_whatsapp()
    print(f"Whatsapp aberto.")

    nome_conversa = conversa(pagina)
    print(f"Conversa Detectada: {nome_conversa}")

    aguardar_gatilho(pagina)
    print("Gatilho executado!")
    
    print("Contagem iniciada...")

    for item in dados:
        mensagem = (
            f"{item['produto']}\n\n"
            f"💰 {item['valor']}\n"
            f"🏷️ {item['cupom']}\n"
            f"🔗 {item['link']}"
        )

        enviar_mensagem(pagina, mensagem)
        registrar_envio()

        time.sleep(intervalo * 60)

    return {
        "status": "envios concluídos",
        "mensagens": obter_contagem()
    }

@router.get("/status")
def status():
    return {
        "mensagens": obter_contagem()
    }