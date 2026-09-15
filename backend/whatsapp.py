from backend.consumer import consumir_planilha

from playwright.sync_api import sync_playwright

def abrir_whatsapp():

    playwright = sync_playwright().start()

    navegador = playwright.chromium.launch(headless=False)

    pagina = navegador.new_page()

    pagina.goto("https://web.whatsapp.com")

    return pagina

def conversa(pagina):

    campo = pagina.locator("[data-testid='conversation-compose-box-input']")

    campo.wait_for(state="visible", timeout=0)

    nome_conversa = campo.get_attribute("aria-label")

    return nome_conversa

def preparar_mensagem(pagina, mensagem):
    campo = pagina.locator(
        "[data-testid='conversation-compose-box-input']"
    )

    campo.fill(mensagem)

    return True

def aguardar_gatilho(pagina):

    botao_enviar = pagina.locator("button[aria-label='Enviar']")

    botao_enviar.wait_for(state="visible", timeout=0)

    botao_enviar.wait_for(state="hidden", timeout=0)

    return True

def enviar_mensagem(pagina, mensagem):

    campo = pagina.locator("[data-testid='conversation-compose-box-input']")

    campo.fill(mensagem)

    botao = pagina.locator("button[aria-label='Enviar']")

    botao.click()

    return True
    
