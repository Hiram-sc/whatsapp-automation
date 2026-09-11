from backend.consumer import consumir_planilha

from playwright.sync_api import sync_playwright

import time
import webbrowser

def abrir_whatsapp():

    playwright = sync_playwright().start()

    navegador = playwright.chromium.launch(headless=False)

    pagina = navegador.new_page()

    pagina.goto("https://web.whatsapp.com")

    return pagina

def enviar_mensagem(pagina, mensagem):
    campo = pagina.locator("div[contenteditable='true']").last

    campo.click()
    campo.fill(mensagem)
    campo.press("Enter")

    return True
    
