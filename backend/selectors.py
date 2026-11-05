import logging
import time

from playwright.sync_api import Locator, Page


logger = logging.getLogger(__name__)

SELETORES_QR_CODE = (
    "div[data-ref] canvas",
    'canvas[aria-label*="QR" i]',
    'canvas[aria-label*="Escaneie" i]',
    'canvas[aria-label*="Scan" i]',
)

SELETORES_PAINEL_WHATSAPP = (
    "#side",
    '[data-testid="chat-list"]',
)

SELETORES_CAMPO_MENSAGEM = (
    '[data-testid="conversation-compose-box-input"]',
    'div[contenteditable="true"][data-tab]',
    'footer div[contenteditable="true"]',
)

SELETORES_BOTAO_ENVIAR = (
    "button[aria-label='Enviar']",
    'button[aria-label="Send"]',
    'button:has(span[data-icon="send"])',
    '[data-testid="send"]',
)

SELETORES_BOTAO_FECHAR_MODAL = (
    'button[aria-label="Fechar"]',
    'button[aria-label="Close"]',
    '[data-testid="x"]',
)

SELETORES_CAMPO_PESQUISA = (
    '[data-testid="chat-list-search-container"] input',
    'div[contenteditable="true"][data-tab="3"]',
    'div[aria-label="Pesquisar"][contenteditable="true"]',
    'div[aria-label="Search"][contenteditable="true"]',
)

SELETOR_RESULTADO_CONVERSA = '[data-testid="cell-frame-container"]'
SELETOR_TITULO_CONVERSA = '[data-testid="cell-frame-title"]'


def primeiro_visivel(pagina: Page, seletores: tuple[str, ...]) -> Locator | None:
    for seletor in seletores:
        try:
            localizador = pagina.locator(seletor).first

            if localizador.count() and localizador.is_visible():
                return localizador
        except Exception:
            logger.debug("Seletor não disponível: %s", seletor, exc_info=True)

    return None


def aguardar_primeiro_visivel(
    pagina: Page,
    seletores: tuple[str, ...],
    timeout_ms: int,
) -> Locator | None:
    limite = time.monotonic() + max(timeout_ms, 0) / 1000

    while True:
        localizador = primeiro_visivel(pagina, seletores)

        if localizador is not None:
            return localizador

        if time.monotonic() >= limite:
            return None

        try:
            pagina.wait_for_timeout(250)
        except Exception:
            logger.debug("Página indisponível durante a espera.", exc_info=True)
            return None
