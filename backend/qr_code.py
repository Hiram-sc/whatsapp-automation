from pathlib import Path
from playwright.sync_api import Page

def capturar_qr_code(pagina: Page) -> bytes | None:
    """
    Captura o QR Code do WhatsApp Web.

    Retorna: 
        bytes: imagem PNG do QR Code
        None: se o QR Code não estiver disponível
    """

    seletor = (
        'canvas[aria-label="Escaneie o QR code para conectar um dispositivo"]'
    )

    qr_code = pagina.locator(seletor).first

    if qr_code.count() == 0:
        return None

    try:
        qr_code.wait_for(state="visible", timeout=10000)
        imagem = qr_code.screenshot()
        return imagem

    except Exception:
        return None
