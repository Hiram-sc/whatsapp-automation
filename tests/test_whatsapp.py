"""
Teste manual do fluxo de conexão e seleção de grupo do WhatsApp.

Execute na raiz do projeto:
    python tests/test_whatsapp.py "Nome exato do grupo"

Por padrão, o script NÃO envia a mensagem. Ele abre o WhatsApp, verifica
o estado, seleciona o grupo e preenche o campo para inspeção.

Para autorizar o clique de envio:
    python tests/test_whatsapp.py "Nome exato do grupo" --enviar

Use somente em um grupo de teste e com uma mensagem não sensível.
"""

import argparse
import time
import sys

from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Adiciona a raiz do projeto ao caminho de importação.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

import backend.whatsapp as whatsapp
from backend.selectors import SELETORES_CAMPO_MENSAGEM, aguardar_primeiro_visivel


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostica conexão, pesquisa de grupo e campo de mensagem."
    )
    parser.add_argument(
        "nome_grupo",
        help="Nome exato do grupo do WhatsApp que será pesquisado."
    )
    parser.add_argument(
        "--mensagem",
        default="Teste da automação. Favor desconsiderar.",
        help="Texto de teste que será preenchido no campo."
    )
    parser.add_argument(
        "--enviar",
        action="store_true",
        help="Pede confirmação antes de clicar em Enviar."
    )
    args = parser.parse_args()

    pagina = None

    try:
        print("\n[1/5] Abrindo/reutilizando o WhatsApp...")
        pagina = whatsapp.abrir_whatsapp()
        print(f"URL atual: {pagina.url}")

        print("\n[2/5] Verificando estado da conexão (até 60 segundos)...")
        estado = "conectando"

        for tentativa in range(60):
            estado = whatsapp.obter_estado_conexao(pagina)
            print(f"Estado: {estado}")

            if estado == "conectado":
                break

            if estado == "aguardando_qr":
                print(
                    "O WhatsApp está aguardando QR Code. "
                    "Escaneie-o na janela do navegador."
                )

            time.sleep(1)

        if estado != "conectado":
            raise RuntimeError(
                f"WhatsApp não ficou conectado. Estado final: {estado}"
            )

        print("\n[3/5] Pesquisando e abrindo o grupo...")
        whatsapp.selecionar_conversa(pagina, args.nome_grupo)
        print(f"Seleção concluída para: {args.nome_grupo}")

        print("\n[4/5] Confirmando o campo de mensagem...")
        campo = aguardar_primeiro_visivel(
            pagina,
            SELETORES_CAMPO_MENSAGEM,
            15000,
        )

        if campo is None:
            raise RuntimeError("O campo de mensagem não ficou visível.")

        print(f"Campo visível: {campo.is_visible()}")
        print(f"aria-label do campo: {campo.get_attribute('aria-label')}")

        print("\n[5/5] Preenchendo mensagem de teste...")
        campo.fill(args.mensagem)
        print("Texto preenchido. Confira visualmente a conversa no navegador.")

        botao_enviar = pagina.locator("button[aria-label='Enviar']")
        print(f"Botão Enviar encontrado: {botao_enviar.count()}")
        print(f"Botão Enviar visível: {botao_enviar.is_visible()}")

        if not args.enviar:
            print(
                "\nMODO SEGURO: a mensagem NÃO foi enviada. "
                "Ela permanece no campo para inspeção."
            )
        else:
            print(
                "\nATENÇÃO: você solicitou o envio. "
                "Confira se o grupo aberto é o correto."
            )
            confirmacao = input(
                "Digite ENVIAR para clicar no botão de envio: "
            )

            if confirmacao == "ENVIAR":
                botao_enviar.wait_for(state="visible", timeout=10000)
                botao_enviar.click()
                print("Clique de envio executado.")
                print(
                    "Confira no WhatsApp se a mensagem apareceu. "
                    "O clique, sozinho, não confirma entrega."
                )
            else:
                print("Envio cancelado; a mensagem não foi clicada.")

        input(
            "\nPressione Enter para encerrar o teste "
            "(a janela do navegador será fechada)..."
        )

    except PlaywrightTimeoutError as erro:
        print(f"\nFALHA: timeout aguardando elemento do WhatsApp: {erro}")
        raise
    except Exception as erro:
        print(f"\nFALHA NO TESTE: {type(erro).__name__}: {erro}")
        raise
    finally:
        # Fecha o contexto iniciado por este script para liberar o perfil.
        # Os dados persistentes da sessão ficam no diretório configurado.
        whatsapp.fechar_whatsapp()


if __name__ == "__main__":
    main()
