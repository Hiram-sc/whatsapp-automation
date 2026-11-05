import logging
import threading

from playwright.sync_api import Page, sync_playwright

from backend import config, status
from backend.qr_code import capturar_qr_code
from backend.selectors import (
    SELETORES_BOTAO_ENVIAR,
    SELETORES_BOTAO_FECHAR_MODAL,
    SELETORES_CAMPO_MENSAGEM,
    SELETORES_CAMPO_PESQUISA,
    SELETORES_PAINEL_WHATSAPP,
    SELETORES_QR_CODE,
    SELETOR_RESULTADO_CONVERSA,
    SELETOR_TITULO_CONVERSA,
    aguardar_primeiro_visivel,
    primeiro_visivel,
)


logger = logging.getLogger(__name__)

_LOCK = threading.RLock()

_playwright = None
_contexto = None
_pagina = None


def _parar_playwright() -> None:
    global _playwright

    playwright = _playwright
    _playwright = None

    if playwright is None:
        return

    try:
        playwright.stop()
        logger.info("Playwright encerrado.")
        
    except Exception:
        logger.exception("Falha ao encerrar o Playwright.")


def abrir_whatsapp() -> Page:
    global _playwright, _contexto, _pagina

    with _LOCK:
        config.SESSION_DIR.mkdir(parents=True, exist_ok=True)

        if _contexto is None:
            if _playwright is not None:
                logger.warning(
                    "Playwright parcialmente inicializado. "
                    "Encerrando antes de tentar novamente."
                )
                _parar_playwright()

            status.definir_conexao("conectando")

            try:
                _playwright = sync_playwright().start()

                opcoes = {
                    "user_data_dir": str(config.SESSION_DIR),
                    "headless": config.PLAYWRIGHT_HEADLESS,
                    "user_agent": config.USER_AGENT,
                    "args": ["--disable-dev-shm-usage"],
                }

                if config.PLAYWRIGHT_CHANNEL:
                    opcoes["channel"] = config.PLAYWRIGHT_CHANNEL

                logger.info(
                    "Iniciando navegador: channel=%s headless=%s sessao=%s",
                    config.PLAYWRIGHT_CHANNEL or "padrão",
                    config.PLAYWRIGHT_HEADLESS,
                    config.SESSION_DIR,
                )

                _contexto = _playwright.chromium.launch_persistent_context(
                    **opcoes
                )
                _contexto.set_default_timeout(config.ELEMENT_TIMEOUT_MS)
                _contexto.set_default_navigation_timeout(
                    config.NAVIGATION_TIMEOUT_MS
                )

                logger.info("Contexto persistente criado com sucesso.")

            except Exception as erro:
                logger.exception(
                    "Falha ao iniciar o navegador com channel=%s.",
                    config.PLAYWRIGHT_CHANNEL or "padrão",
                )
                _contexto = None
                _pagina = None
                _parar_playwright()
                status.definir_conexao("erro")

                raise RuntimeError(
                    "Não foi possível iniciar o navegador do WhatsApp. "
                    "Verifique se o Chromium do Playwright está instalado "
                    "e se o diretório de sessão é gravável."
                ) from erro

        try:
            if _pagina is None or _pagina.is_closed():
                paginas = _contexto.pages

                if paginas:
                    _pagina = paginas[0]
                else:
                    _pagina = _contexto.new_page()
        except Exception as erro:
            logger.exception("Contexto do navegador está inválido.")
            _contexto = None
            _pagina = None
            _parar_playwright()
            status.definir_conexao("erro")
            raise RuntimeError(
                "O navegador do WhatsApp está indisponível. "
                "Tente novamente."
            ) from erro

        try:
            if not _pagina.url.startswith(config.WHATSAPP_URL):
                logger.info("Navegando para %s", config.WHATSAPP_URL)
                _pagina.goto(
                    config.WHATSAPP_URL,
                    wait_until="domcontentloaded",
                    timeout=config.NAVIGATION_TIMEOUT_MS,
                )
        except Exception as erro:
            logger.exception("Falha ao abrir o WhatsApp Web.")
            status.definir_conexao("erro")
            raise RuntimeError(
                "Não foi possível abrir o WhatsApp Web."
            ) from erro

        logger.info(
            "WhatsApp disponível: url=%s título=%s",
            _pagina.url,
            _pagina.title(),
        )

        return _pagina


def fechar_whatsapp() -> None:
    global _playwright, _contexto, _pagina

    with _LOCK:
        pagina = _pagina
        contexto = _contexto
        playwright = _playwright

        _pagina = None
        _contexto = None
        _playwright = None

        if pagina is not None:
            try:
                if not pagina.is_closed():
                    pagina.close()
            except Exception:
                logger.debug("Falha ao fechar a página.", exc_info=True)

        if contexto is not None:
            try:
                contexto.close()
                logger.info("Contexto do navegador fechado.")
            except Exception:
                logger.exception("Falha ao fechar o contexto do navegador.")

        if playwright is not None:
            try:
                playwright.stop()
                logger.info("Playwright encerrado.")
            except Exception:
                logger.exception("Falha ao encerrar o Playwright.")

        status.definir_conexao("desconectado")


def obter_estado_conexao(pagina: Page | None) -> str:
    if pagina is None or pagina.is_closed():
        estado = "desconectado"
    else:
        try:
            if primeiro_visivel(pagina, SELETORES_QR_CODE) is not None:
                estado = "aguardando_qr"
            elif primeiro_visivel(pagina, SELETORES_PAINEL_WHATSAPP) is not None:
                estado = "conectado"
            else:
                estado = "conectando"
        except Exception:
            logger.exception("Falha ao verificar o estado da conexão.")
            status.definir_conexao("erro")
            return "erro"

    status.definir_conexao(estado)
    return estado


def obter_qr_code(pagina: Page) -> bytes | None:
    estado = obter_estado_conexao(pagina)

    if estado == "conectado":
        return None

    if estado == "desconectado":
        raise RuntimeError("O navegador do WhatsApp não está aberto.")

    imagem = capturar_qr_code(pagina, timeout_ms=config.QR_WAIT_TIMEOUT_MS)

    if imagem is not None:
        return imagem

    estado_atual = obter_estado_conexao(pagina)

    if estado_atual == "conectado":
        return None

    raise RuntimeError(
        "O QR Code ainda não está disponível. "
        f"Estado atual do WhatsApp: {estado_atual}."
    )


def fechar_modal_inicial(pagina: Page) -> bool:
    dialogos = pagina.locator('[role="dialog"]')

    for indice in range(dialogos.count()):
        dialogo = dialogos.nth(indice)

        if not dialogo.is_visible():
            continue

        for seletor in SELETORES_BOTAO_FECHAR_MODAL:
            botao = dialogo.locator(seletor).first

            if botao.count() and botao.is_visible():
                botao.click(timeout=3000)
                dialogo.wait_for(state="hidden", timeout=5000)
                logger.info("Modal inicial do WhatsApp fechado.")
                return True

        raise RuntimeError(
            "Um modal está bloqueando o WhatsApp, mas não foi possível "
            "identificar o botão de fechar."
        )

    return False


def selecionar_conversa(pagina: Page, nome_grupo: str) -> bool:
    campo_pesquisa = aguardar_primeiro_visivel(
        pagina,
        SELETORES_CAMPO_PESQUISA,
        config.ELEMENT_TIMEOUT_MS,
    )

    if campo_pesquisa is None:
        raise RuntimeError(
            "Não foi possível localizar o campo de pesquisa do WhatsApp."
        )

    campo_pesquisa.fill(nome_grupo)

    resultados = pagina.locator(SELETOR_RESULTADO_CONVERSA).filter(
        has=pagina.locator(SELETOR_TITULO_CONVERSA).get_by_text(
            nome_grupo,
            exact=True,
        )
    )

    try:
        resultados.first.wait_for(
            state="visible",
            timeout=config.ELEMENT_TIMEOUT_MS,
        )
    except Exception as erro:
        logger.warning(
            "Grupo não encontrado: %s",
            nome_grupo,
            exc_info=True,
        )
        raise RuntimeError(
            f'Não foi encontrado um grupo com o nome "{nome_grupo}".'
        ) from erro

    quantidade = resultados.count()

    if quantidade > 1:
        raise RuntimeError(
            f'Foi encontrado mais de um resultado com o nome "{nome_grupo}".'
        )

    resultados.first.click()

    campo_mensagem = aguardar_primeiro_visivel(
        pagina,
        SELETORES_CAMPO_MENSAGEM,
        config.ELEMENT_TIMEOUT_MS,
    )

    if campo_mensagem is None:
        raise RuntimeError(
            "O grupo foi aberto, mas o campo de mensagem não ficou visível."
        )

    logger.info('Grupo "%s" aberto com sucesso.', nome_grupo)
    return True


def enviar_mensagem(pagina: Page, mensagem: str) -> bool:
    campo = aguardar_primeiro_visivel(
        pagina,
        SELETORES_CAMPO_MENSAGEM,
        config.ELEMENT_TIMEOUT_MS,
    )

    if campo is None:
        raise RuntimeError("O campo de mensagem não está disponível.")

    campo.fill(mensagem)

    botao = aguardar_primeiro_visivel(
        pagina,
        SELETORES_BOTAO_ENVIAR,
        config.ELEMENT_TIMEOUT_MS,
    )

    if botao is None:
        raise RuntimeError(
            "O botão de enviar não ficou disponível após preencher a mensagem."
        )

    botao.click()
    return True
