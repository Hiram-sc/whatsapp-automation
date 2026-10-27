from fastapi import APIRouter, UploadFile, File, Form
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response

from pathlib import Path

from backend.whatsapp import abrir_whatsapp, obter_qr_code, conversa, aguardar_gatilho, enviar_mensagem
from backend.consumer import consumir_planilha 
from backend.status import zerar_contagem, registrar_envio, obter_contagem

import asyncio

from concurrent.futures import ThreadPoolExecutor

import time
import shutil

router = APIRouter()

PLAYWRIGHT_EXECUTOR = ThreadPoolExecutor(max_workers=1)

UPLOAD_DIR = Path("uploads") 
UPLOAD_DIR.mkdir(exist_ok=True) 

@router.get("/")
def painel():
    return FileResponse("front/index.html")

@router.get("/whatsapp/qrcode")
async def obter_imagem_qr():

    loop = asyncio.get_running_loop()

    imagem = await loop.run_in_executor(
        PLAYWRIGHT_EXECUTOR,
        capturar_imagem_qr
    )

    if imagem is None:
        raise HTTPException(
            status_code=503,
            detail="QR Code ainda não está disponível."
        )

    return Response(
        content=imagem,
        media_type="image/png"
    )


def capturar_imagem_qr():
    pagina = abrir_whatsapp()
    return obter_qr_code(pagina)

def executar_automacao(dados, intervalo):
    pagina = abrir_whatsapp()

    nome_conversa = conversa(pagina)
    print(f"Conversa detectada: {nome_conversa}")

    aguardar_gatilho(pagina)

    for item in dados:
        valor = item["valor"]
        valor_formatado = (
            f"{valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        mensagem = (
            f"🔥 {item['produto']}\n\n"
            f"💸 R$ {valor_formatado}\n"
            f"🎟️ Cupom: {item['cupom']}\n"
            f"{item['link']}"
        )

        enviar_mensagem(pagina, mensagem)
        registrar_envio()
        time.sleep(intervalo * 60)

    return obter_contagem()

@router.post("/iniciar")
async def whatsapp(
    planilha: UploadFile = File(...),
    intervalo: int = Form(...)
):

    caminho_arquivo = UPLOAD_DIR / planilha.filename

    with caminho_arquivo.open("wb") as arquivo:
        shutil.copyfileobj(planilha.file, arquivo)

    print("Consumindo planilha...")
    dados = consumir_planilha(caminho_arquivo)

    loop = asyncio.get_running_loop()

    mensagens = await loop.run_in_executor(
        PLAYWRIGHT_EXECUTOR,
        executar_automacao,
        dados,
        intervalo
    )

    return {
        "status": "envios concluídos",
        "mensagens": mensagens
    }
@router.get("/status")
def status():
    return {
        "mensagens": obter_contagem()
    }