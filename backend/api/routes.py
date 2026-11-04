
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, Response

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import asyncio
import shutil
import time

from backend.whatsapp import (
    abrir_whatsapp,
    obter_qr_code,
    obter_estado_conexao,
    fechar_modal_inicial,
    selecionar_conversa,
    enviar_mensagem
)

from backend.consumer import consumir_planilha

from backend.status import (
    zerar_contagem,
    registrar_envio,
    obter_contagem
)


router = APIRouter()

PLAYWRIGHT_EXECUTOR = ThreadPoolExecutor(max_workers=1)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/")
def painel():
    return FileResponse("front/index.html")


def capturar_imagem_qr():
    pagina = abrir_whatsapp()
    return obter_qr_code(pagina)


def consultar_estado_whatsapp():
    pagina = abrir_whatsapp()
    return obter_estado_conexao(pagina)


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


@router.get("/whatsapp/estado")
async def estado_whatsapp():
    loop = asyncio.get_running_loop()

    estado = await loop.run_in_executor(
        PLAYWRIGHT_EXECUTOR,
        consultar_estado_whatsapp
    )

    return {"estado": estado}


def executar_automacao(dados, intervalo, nome_grupo):
    pagina = abrir_whatsapp()

    estado = obter_estado_conexao(pagina)

    if estado != "conectado":
        raise RuntimeError(
            f"WhatsApp não está conectado. Estado atual: {estado}."
        )

    fechar_modal_inicial(pagina)

    selecionar_conversa(pagina, nome_grupo)

    print(f"Grupo aberto: {nome_grupo}")
    print("Campo de mensagem disponível.")

    for indice, item in enumerate(dados):

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

        print(
            f"Mensagem {indice + 1}/{len(dados)} enviada."
        )

        if indice < len(dados) - 1 and intervalo > 0:
            time.sleep(intervalo * 60)

    return obter_contagem()


@router.post("/iniciar")
async def whatsapp(
    planilha: UploadFile = File(...),
    intervalo: float = Form(...),
    nome_grupo: str = Form(...)
):

    if intervalo < 0:
        raise HTTPException(
            status_code=400,
            detail="O intervalo não pode ser negativo."
        )

    if not nome_grupo.strip():
        raise HTTPException(
            status_code=400,
            detail="Informe o nome do grupo."
        )

    nome_arquivo = Path(planilha.filename).name

    caminho_arquivo = UPLOAD_DIR / nome_arquivo

    with caminho_arquivo.open("wb") as arquivo:
        shutil.copyfileobj(planilha.file, arquivo)

    await planilha.close()

    print("Consumindo planilha...")

    dados = consumir_planilha(caminho_arquivo)

    if not dados:
        raise HTTPException(
            status_code=400,
            detail="A planilha não contém mensagens para enviar."
        )

    loop = asyncio.get_running_loop()

    # Verifica a conexão antes de iniciar a automação.
    estado = await loop.run_in_executor(
        PLAYWRIGHT_EXECUTOR,
        consultar_estado_whatsapp
    )

    if estado != "conectado":
        raise HTTPException(
            status_code=409,
            detail=f"WhatsApp não está conectado. Estado atual: {estado}."
        )

    zerar_contagem()

    mensagens = await loop.run_in_executor(
        PLAYWRIGHT_EXECUTOR,
        executar_automacao,
        dados,
        intervalo,
        nome_grupo.strip()
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
