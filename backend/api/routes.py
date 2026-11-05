import asyncio
import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from backend import config, status
from backend.consumer import consumir_planilha
from backend.whatsapp import (
    abrir_whatsapp,
    enviar_mensagem,
    fechar_modal_inicial,
    fechar_whatsapp,
    obter_estado_conexao,
    obter_qr_code,
    selecionar_conversa,
)


logger = logging.getLogger(__name__)

router = APIRouter()

PLAYWRIGHT_EXECUTOR = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="whatsapp-playwright",
)

_AUTOMATION_TASK: asyncio.Task | None = None


config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validar_intervalo(intervalo: float) -> float:
    if not math.isfinite(intervalo):
        raise HTTPException(
            status_code=400,
            detail="O intervalo precisa ser um número válido.",
        )

    if intervalo < config.INTERVALO_MINIMO_MINUTOS:
        raise HTTPException(
            status_code=400,
            detail=(
                "O intervalo mínimo entre mensagens é "
                f"{config.INTERVALO_MINIMO_MINUTOS:g} minuto(s)."
            ),
        )

    if intervalo > config.INTERVALO_MAXIMO_MINUTOS:
        raise HTTPException(
            status_code=400,
            detail=(
                "O intervalo máximo entre mensagens é "
                f"{config.INTERVALO_MAXIMO_MINUTOS:g} minuto(s)."
            ),
        )

    return intervalo


def _validar_grupo(nome_grupo: str) -> str:
    nome = nome_grupo.strip()

    if not nome:
        raise HTTPException(
            status_code=400,
            detail="Informe o nome do grupo.",
        )

    if len(nome) > config.MAX_NOME_GRUPO:
        raise HTTPException(
            status_code=400,
            detail=(
                "O nome do grupo deve ter no máximo "
                f"{config.MAX_NOME_GRUPO} caracteres."
            ),
        )

    return nome


def _nome_arquivo_temporario(planilha: UploadFile) -> str:
    nome_original = Path(planilha.filename or "").name

    if not nome_original:
        raise HTTPException(
            status_code=400,
            detail="Selecione um arquivo de planilha.",
        )

    if not nome_original.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Envie uma planilha no formato .xlsx.",
        )

    return f"{uuid4().hex}.xlsx"


def _salvar_upload(arquivo, destino: Path) -> int:
    total = 0

    try:
        with destino.open("wb") as saida:
            while bloco := arquivo.read(1024 * 1024):
                total += len(bloco)

                if total > config.MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "A planilha excede o tamanho máximo permitido de "
                            f"{config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
                        ),
                    )

                saida.write(bloco)
    except OSError as erro:
        logger.exception("Não foi possível salvar a planilha enviada.")
        raise HTTPException(
            status_code=400,
            detail="Não foi possível salvar a planilha enviada.",
        ) from erro

    return total


def _remover_arquivo(caminho: Path) -> None:
    try:
        caminho.unlink(missing_ok=True)
    except OSError:
        logger.warning("Não foi possível remover o arquivo %s.", caminho)


def _formatar_valor(valor: float) -> str:
    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def _montar_mensagem(item: dict) -> str:
    return (
        f"🔥 {item['produto']}\n\n"
        f"💸 R$ {_formatar_valor(item['valor'])}\n"
        f"🎟️ Cupom: {item['cupom']}\n"
        f"{item['link']}"
    )


def capturar_imagem_qr():
    pagina = abrir_whatsapp()
    return obter_qr_code(pagina)


def consultar_estado_whatsapp():
    pagina = abrir_whatsapp()
    return obter_estado_conexao(pagina)


def executar_automacao(dados, intervalo, nome_grupo):
    status.marcar_em_execucao()

    try:
        pagina = abrir_whatsapp()

        fechar_modal_inicial(pagina)
        selecionar_conversa(pagina, nome_grupo)

        logger.info(
            'Automação iniciada para o grupo "%s" com %s mensagem(ns).',
            nome_grupo,
            len(dados),
        )

        for indice, item in enumerate(dados):
            enviar_mensagem(pagina, _montar_mensagem(item))
            status.registrar_envio()

            logger.info(
                "Mensagem %s/%s enviada.",
                indice + 1,
                len(dados),
            )

            if indice < len(dados) - 1 and intervalo > 0:
                time.sleep(intervalo * 60)

        status.finalizar_automacao()
        logger.info(
            "Automação concluída: %s mensagem(ns) enviada(s).",
            status.obter_status()["mensagens_enviadas"],
        )
        
    except Exception as erro:
        logger.exception("Falha durante a automação.")
        status.falhar_automacao(str(erro))
        raise


async def _executar_automacao_background(dados, intervalo, nome_grupo):
    global _AUTOMATION_TASK

    tarefa_atual = asyncio.current_task()

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            PLAYWRIGHT_EXECUTOR,
            executar_automacao,
            dados,
            intervalo,
            nome_grupo,
        )
        
    except Exception:
        logger.exception("A automação foi encerrada com erro.")
    finally:
        if _AUTOMATION_TASK is tarefa_atual:
            _AUTOMATION_TASK = None


async def encerrar_recursos() -> None:
    if not status.automacao_ativa():
        loop = asyncio.get_running_loop()

        try:
            await asyncio.wait_for(
                loop.run_in_executor(PLAYWRIGHT_EXECUTOR, fechar_whatsapp),
                timeout=10,
            )

        except Exception:
            logger.exception("Não foi possível encerrar o navegador no shutdown.")

    PLAYWRIGHT_EXECUTOR.shutdown(wait=False, cancel_futures=True)


@router.get("/")
def painel():
    return FileResponse(config.INDEX_FILE)


@router.get("/whatsapp/qrcode")
async def obter_imagem_qr():
    loop = asyncio.get_running_loop()

    try:
        imagem = await loop.run_in_executor(
            PLAYWRIGHT_EXECUTOR,
            capturar_imagem_qr,
        )

    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro

    if imagem is None:
        estado = status.obter_status()["conexao"]

        if estado == "conectado":
            raise HTTPException(
                status_code=409,
                detail="O WhatsApp já está conectado.",
            )

        raise HTTPException(
            status_code=503,
            detail=(
                "QR Code ainda não está disponível. "
                f"Estado atual do WhatsApp: {estado}."
            ),
        )

    return Response(
        content=imagem,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/whatsapp/estado")
async def estado_whatsapp():
    loop = asyncio.get_running_loop()

    try:
        estado = await loop.run_in_executor(
            PLAYWRIGHT_EXECUTOR,
            consultar_estado_whatsapp,
        )

    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro

    return {
        "estado": estado,
        "conexao": status.obter_status()["conexao"],
    }


@router.post("/iniciar", status_code=202)
async def whatsapp(
    planilha: UploadFile = File(...),
    intervalo: float = Form(...),
    nome_grupo: str = Form(...),
):
    global _AUTOMATION_TASK

    intervalo_validado = _validar_intervalo(intervalo)
    grupo = _validar_grupo(nome_grupo)
    nome_arquivo = _nome_arquivo_temporario(planilha)

    if status.automacao_ativa():
        raise HTTPException(
            status_code=409,
            detail="Já existe uma automação em andamento.",
        )

    caminho_arquivo = config.UPLOAD_DIR / nome_arquivo

    try:
        await asyncio.to_thread(
            _salvar_upload,
            planilha.file,
            caminho_arquivo,
        )

        try:
            dados = await asyncio.to_thread(
                consumir_planilha,
                caminho_arquivo,
            )
            
        except ValueError as erro:
            raise HTTPException(status_code=400, detail=str(erro)) from erro
    finally:
        try:
            await planilha.close()
        except Exception:
            logger.warning("Não foi possível fechar o upload recebido.")

        _remover_arquivo(caminho_arquivo)

    loop = asyncio.get_running_loop()

    try:
        estado = await loop.run_in_executor(
            PLAYWRIGHT_EXECUTOR,
            consultar_estado_whatsapp,
        )
        
    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro

    if estado != "conectado":
        raise HTTPException(
            status_code=409,
            detail=(
                "WhatsApp não está conectado. "
                f"Estado atual: {estado}. "
                "Conecte o WhatsApp antes de iniciar."
            ),
        )

    if not status.reservar_automacao(len(dados)):
        raise HTTPException(
            status_code=409,
            detail="Já existe uma automação em andamento.",
        )

    _AUTOMATION_TASK = asyncio.create_task(
        _executar_automacao_background(
            dados,
            intervalo_validado,
            grupo,
        )
    )

    return {
        "status": "iniciada",
        "total": len(dados),
        "intervalo": intervalo_validado,
    }


@router.get("/status")
def status_geral():
    return status.obter_status()
