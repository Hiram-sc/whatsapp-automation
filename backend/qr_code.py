import logging

from playwright.sync_api import Page

from backend import config
from backend.selectors import SELETORES_QR_CODE, aguardar_primeiro_visivel


logger = logging.getLogger(__name__)


def capturar_qr_code(pagina: Page, timeout_ms: int | None = None,) -> bytes | None:
    
    limite_ms = timeout_ms if timeout_ms is not None else config.QR_WAIT_TIMEOUT_MS
    qr_code = aguardar_primeiro_visivel(pagina, SELETORES_QR_CODE, limite_ms)

    if qr_code is None:
        logger.info("QR Code não encontrado após %sms.", limite_ms)
        return None

    try:
        imagem = qr_code.screenshot()
        logger.info("QR Code capturado com sucesso.")
        return imagem
    
    except Exception as erro:
        logger.exception("Falha ao capturar a imagem do QR Code.")
        raise RuntimeError(
            "Não foi possível capturar a imagem do QR Code."
        ) from erro
