"""
Smoke test do navegador com um diretório de sessão temporário.

Execute na raiz do projeto:
    python tests/test_playwright_smoke.py

O teste não usa a sessão real e não envia mensagens.
"""

import os
import sys
import tempfile
import time
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))


def main():
    with tempfile.TemporaryDirectory(prefix="whatsapp-smoke-") as diretorio:
        os.environ["WHATSAPP_SESSION_DIR"] = diretorio
        os.environ.setdefault("PLAYWRIGHT_HEADLESS", "true")
        os.environ.setdefault("PLAYWRIGHT_CHANNEL", "chromium")

        import backend.config as config
        import backend.whatsapp as whatsapp

        pagina = None

        try:
            print("Abrindo WhatsApp Web em sessão temporária...")
            pagina = whatsapp.abrir_whatsapp()

            print(f"URL: {pagina.url}")
            print(f"Título: {pagina.title()}")
            print(f"UA: {pagina.evaluate('navigator.userAgent')}")
            print(f"Idioma: {pagina.evaluate('navigator.language')}")
            print(f"Sessão: {config.SESSION_DIR}")

            estado = "conectando"

            for _ in range(20):
                estado = whatsapp.obter_estado_conexao(pagina)
                print(f"Estado: {estado}")

                if estado in {"aguardando_qr", "conectado"}:
                    break

                time.sleep(1)

            if estado == "aguardando_qr":
                imagem = whatsapp.obter_qr_code(pagina)
                print(f"QR capturado: {len(imagem) if imagem else 0} bytes")
            elif estado == "conectado":
                print("WhatsApp já está conectado nesta sessão temporária.")
            else:
                raise RuntimeError(
                    f"Não foi possível identificar o estado do WhatsApp: {estado}"
                )

        finally:
            print("Encerrando navegador...")
            whatsapp.fechar_whatsapp()

            if pagina is not None and not pagina.is_closed():
                raise RuntimeError("A página não foi fechada corretamente.")


if __name__ == "__main__":
    main()
