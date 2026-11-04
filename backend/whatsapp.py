
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from backend.qr_code import capturar_qr_code


DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
DIRETORIO_SESSAO = DIRETORIO_PROJETO / "session"

_playwright = None
_contexto = None
_pagina = None

SELETOR_QR_CODE = (
    'canvas[aria-label="Escaneie o QR code para conectar um dispositivo"]'
)

SELETOR_PAINEL_WHATSAPP = "#side"

SELETOR_CAMPO_MENSAGEM = (
    '[data-testid="conversation-compose-box-input"]'
)


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
        carregando: estado ainda não identificado.
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
    if obter_estado_conexao(pagina) != "aguardando_qr":
        return None

    return capturar_qr_code(pagina)

def fechar_modal_inicial(pagina: Page):
    dialogos = pagina.locator('[role="dialog"]')

    for indice in range(dialogos.count()):
        dialogo = dialogos.nth(indice)

        if not dialogo.is_visible():
            continue

        botoes_fechar = [
            'button[aria-label="Fechar"]',
            'button[aria-label="Close"]',
            '[data-testid="x"]'
        ]

        for seletor in botoes_fechar:
            botao = dialogo.locator(seletor).first

            if botao.count() and botao.is_visible():
                botao.click(timeout=3000)
                dialogo.wait_for(state="hidden", timeout=5000)

                print("Modal inicial fechado.")
                return True

        raise RuntimeError(
            "Um modal está bloqueando o WhatsApp, "
            "mas não foi possível identificar seu botão de fechar."
        )

    return False


def selecionar_conversa(pagina: Page, nome_grupo: str):
    campo_pesquisa = pagina.locator(
        '[data-testid="chat-list-search-container"] input'
    )

    campo_pesquisa.wait_for(state="visible", timeout=15000)
    campo_pesquisa.fill(nome_grupo)

    resultados = pagina.locator(
        '[data-testid="cell-frame-container"]'
    ).filter(
        has=pagina.locator(
            '[data-testid="cell-frame-title"]'
        ).get_by_text(nome_grupo, exact=True)
    )

    try:
        resultados.first.wait_for(
            state="visible",
            timeout=15000
        )
    except Exception:
        raise RuntimeError(
            f'Não foi encontrado um grupo com o nome "{nome_grupo}".'
        )

    quantidade = resultados.count()

    if quantidade > 1:
        raise RuntimeError(
            f'Foi encontrado mais de um resultado com o nome "{nome_grupo}".'
        )

    resultados.first.click()

    campo_mensagem = pagina.locator(SELETOR_CAMPO_MENSAGEM)
    campo_mensagem.wait_for(state="visible", timeout=15000)

    print(f'Grupo "{nome_grupo}" aberto com sucesso.')

    return True

def conversa(pagina: Page):
    campo = pagina.locator(SELETOR_CAMPO_MENSAGEM)

    campo.wait_for(state="visible", timeout=15000)

    return campo.get_attribute("aria-label")


def preparar_mensagem(pagina: Page, mensagem: str):
    campo = pagina.locator(SELETOR_CAMPO_MENSAGEM)

    campo.wait_for(state="visible", timeout=15000)
    campo.fill(mensagem)

    return True


def enviar_mensagem(pagina: Page, mensagem: str):
    campo = pagina.locator(SELETOR_CAMPO_MENSAGEM)

    campo.wait_for(state="visible", timeout=15000)
    campo.fill(mensagem)

    botao = pagina.locator("button[aria-label='Enviar']")

    botao.wait_for(state="visible", timeout=10000)
    botao.click()

    return True
