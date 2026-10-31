from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from backend.qr_code import capturar_qr_code

import time


DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
DIRETORIO_SESSAO = DIRETORIO_PROJETO / "session"

_playwright = None
_contexto = None
_pagina = None

SELETOR_QR_CODE = (
    'canvas[aria-label="Escaneie o QR code para conectar um dispositivo"]'
)

SELETOR_PAINEL_WHATSAPP = "#side"

def abrir_whatsapp() -> Page:
    global _playwright, _contexto, _pagina

    if _contexto is None:
        _playwright = sync_playwright().start()

        _contexto = _playwright.chromium.launch_persistent_context(
            user_data_dir=str(DIRETORIO_SESSAO),
            headless=True,
            channel="chrome"
        )

    if _pagina is None or _pagina.is_closed():
        paginas = _contexto.pages

        if paginas:
            _pagina = paginas[0]
        else:
            _pagina = _contexto.new_page()

    if _pagina.url == "about:blank":
        _pagina.goto("https://web.whatsapp.com")

    return _pagina

def obter_estado_conexao(pagina: Page) -> str:
    """
    Retorna:
        aguardando_qr: QR Code visível.
        conectado: interface principal do WhatsApp visível.
        carregando: ainda não foi possível identificar o estado.
    """

    try: 
        qr_code = pagina.locator(SELETOR_QR_CODE).first

        if qr_code.is_visible():
            return "aguardando_qr"

        painel = pagina.locator(SELETOR_PAINEL_WHATSAPP)

        if painel.is_visible():
            return "conectado"

    except Exception as erro:
        print(f"Erro ao verificar conexão: {erro}")

    return "carregando"

def obter_qr_code(pagina: Page) -> bytes | None:
    """
    Retorna a imagem PNG do QR Code, quando disponível.
    """

    if obter_estado_conexao(pagina) != "aguardando_qr":
        return None

    return capturar_qr_code(pagina)

def selecionar_conversa(pagina: Page, nome_grupo: str):
    campo_pesquisa = pagina.locator(
        'input[aria-label="Pesquisar ou começar uma nova conversa"]'
    )

    campo_pesquisa.wait_for(state="visible")

    campo_pesquisa.fill(nome_grupo)

    resultados = pagina.locator(
        '[data-testid="cell-frame-container"]'
    ).filter(
        has=pagina.locator(
            f'[data-testid="cell-frame-title"]'
        ).get_by_text(nome_grupo, exact=True)
    )
    
    return 
 
def conversa(pagina: Page):

    campo = pagina.locator("[data-testid='conversation-compose-box-input']")

    campo.wait_for(state="visible", timeout=0)

    return campo.get_attribute("aria-label")

def preparar_mensagem(pagina: Page, mensagem: str):
    campo = pagina.locator("[data-testid='conversation-compose-box-input']")

    campo.fill(mensagem)

    return True

def enviar_mensagem(pagina: Page, mensagem: str):

    campo = pagina.locator("[data-testid='conversation-compose-box-input']")

    campo.fill(mensagem)

    botao = pagina.locator("button[aria-label='Enviar']")

    time.sleep(3)

    botao.click()

    return True
    
