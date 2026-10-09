# Automação de mensagens via WhatsApp Web

## Apresentação do projeto

Esta aplicação automatiza o envio de mensagens pelo **WhatsApp Web** a partir dos dados de uma **planilha Excel**. A ideia é evitar o envio manual e repetitivo: o usuário monta uma planilha com os produtos/promoções que deseja divulgar, faz o upload pelo painel web, define o intervalo entre as mensagens e inicia a automação. O backend lê a planilha, abre o WhatsApp Web no navegador, monta uma mensagem para cada linha da planilha e a envia para a conversa que estiver aberta.

O problema que o projeto resolve é o de **disparar um lote de mensagens padronizadas** (produto, valor, cupom e link) sem precisar digitar cada uma manualmente. O funcionamento geral é:

1. O usuário acessa o painel HTML servido pelo FastAPI.
2. Envia uma planilha `.xlsx` e um intervalo em minutos.
3. O backend lê a planilha com o Pandas.
4. O Playwright abre o WhatsApp Web (Chromium visível).
5. O usuário autentica/abre a conversa manualmente.
6. A automação monta e envia uma mensagem por linha da planilha, respeitando o intervalo, e atualiza um contador.

> Observação: o login no WhatsApp Web é **manual**. O projeto não captura o QR Code no painel nem persiste a sessão em um perfil dedicado (ver *Limitações e estado atual*).

---

## Tecnologias utilizadas

As versões abaixo foram retiradas de `requirements.txt`.

| Tecnologia | Versão | Função no projeto |
| --- | --- | --- |
| Python | 3.13 (compatível) | Linguagem de implementação do backend. |
| FastAPI | 0.141.1 | Framework web que expõe as rotas HTTP e serve o painel. |
| Uvicorn | 0.52.4 | Servidor ASGI usado para executar a aplicação FastAPI. |
| Starlette | 1.6.0 | Base web do FastAPI (dependência interna). |
| Playwright | 1.62.0 | Automação do navegador para controlar o WhatsApp Web. |
| Pandas | 3.0.5 | Leitura e iteração sobre os dados da planilha. |
| OpenPyXL | 3.1.5 | Engine usada pelo Pandas para ler arquivos `.xlsx`. |
| python-multipart | 0.0.32 | Necessário para receber o upload de arquivos via `multipart/form-data`. |
| HTML / CSS / JavaScript | — | Interface do painel (`front/`), sem frameworks (JS puro). |

Dependências transitivas presentes no `requirements.txt`: `annotated-doc`, `annotated-types`, `anyio`, `click`, `et_xmlfile`, `greenlet`, `h11`, `idna`, `numpy`, `pydantic`, `pydantic_core`, `pyee`, `python-dateutil`, `six`, `typing-inspection`, `typing_extensions`, `tzdata`.

---

## Funcionalidades atuais

Legenda: **Implementado** = presente e ativo; **Parcial** = presente, mas com ressalvas; **Não implementado** = ausente no código.

| Funcionalidade | Estado | Localização |
| --- | --- | --- |
| Upload de planilha pela interface | Implementado | `front/index.html:41`, `front/static/js/painel.js:15` |
| Recebimento do arquivo pelo backend | Implementado | `backend/api/routes.py:22` (`UploadFile`) |
| Salvamento do upload em `uploads/` | Implementado | `backend/api/routes.py:28-31` |
| Leitura dos dados da planilha | Implementado | `backend/consumer.py:5` (`pd.read_excel`) |
| Identificação das colunas | Implementado | `backend/consumer.py:11-14` |
| Montagem das mensagens | Implementado | `backend/api/routes.py:50-55` |
| Formatação do valor monetário | Implementado | `backend/api/routes.py:52` (segue o padrão brasileiro) |
| Abertura do WhatsApp Web | Implementado | `backend/whatsapp.py:7-17` |
| Detecção da conversa aberta | Implementado | `backend/whatsapp.py:19-27` |
| "Gatilho" de espera | Implementado | `backend/whatsapp.py:36-44` |
| Envio da mensagem | Implementado | `backend/whatsapp.py:46-58` |
| Intervalo entre envios | Implementado | `backend/api/routes.py:60` |
| Contagem de mensagens enviadas | Implementado | `backend/status.py` |
| Atualização do contador na interface | Implementado | `front/static/js/painel.js:32-38` |
| Atualização do "Tempo percorrido" | Não implementado | `front/index.html:27` (valor fixo `00:00:00`) |
| Tratamento de erros | Parcial | Apenas `print`; sem `try/except` nem `HTTPException` |
| Captura de QR Code no painel | Não implementado | — |
| Persistência de sessão do WhatsApp | Não implementado | `session/` existe, mas está vazio e não é usado no código |

Detalhes importantes confirmados no código:

- **Colunas obrigatórias**: `PRODUTO`, `VALOR`, `CUPOM`, `LINK` (`backend/consumer.py:11-14`). Se alguma não existir, o Pandas lança `KeyError` (não há validação/tratamento).
- **Intervalo em minutos**: o valor recebido é multiplicado por 60 em `time.sleep(intervalo * 60)` (`backend/api/routes.py:60`).
- **Contador em memória**: o dicionário `STATUS` é definido no módulo `backend/status.py` e é zerado a cada chamada de `/iniciar`, sendo perdido quando o servidor reinicia.
- **Formatação monetária**: o valor é formatado no **padrão brasileiro**, com o símbolo `R$`, ponto como separador de milhar e vírgula como separador decimal (ex.: `R$ 1.299,90`).

---

## Fluxo de funcionamento passo a passo

A ordem real de execução, conforme `backend/api/routes.py`, é:

1. **Acesso à interface** — o usuário abre `GET /`, que retorna `front/index.html`.
2. **Seleção da planilha** — o usuário anexa um arquivo `.xlsx` (input `accept=".xlsx"`); o JavaScript apenas exibe o nome do arquivo (`front/static/js/painel.js:4-10`).
3. **Envio** — ao clicar em **Iniciar**, o frontend monta um `FormData` com os campos `planilha` e `intervalo` e faz `POST /iniciar` (`front/static/js/painel.js:15-29`).
4. **Recebimento do arquivo** — o backend salva o arquivo em `uploads/` mantendo o nome original (`backend/api/routes.py:28-31`).
5. **Processamento dos dados** — `consumir_planilha` lê o Excel e devolve uma lista de dicionários (`backend/consumer.py`).
6. **Zerar contador** — `zerar_contagem()` reinicia o contador (`backend/api/routes.py:36`).
7. **Inicialização do navegador** — `abrir_whatsapp()` inicia o Playwright, abre o Chromium com `headless=False` e navega para `https://web.whatsapp.com` (`backend/whatsapp.py:7-17`).
8. **Autenticação / preparação** — como o navegador é visível, o usuário faz login no WhatsApp Web manualmente (lendo o QR Code na própria janela do navegador).
9. **Detecção da conversa** — `conversa(pagina)` aguarda o campo de digitação ficar visível e lê o atributo `aria-label` (nome da conversa aberta), imprimindo-o no console (`backend/whatsapp.py:19-27`). A conversa de destino é a que estiver aberta no WhatsApp Web; não há busca/seleção automática de contato.
10. **Gatilho** — `aguardar_gatilho(pagina)` aguarda o botão com `aria-label='Enviar'` ficar visível e depois oculto (`backend/whatsapp.py:36-44`). Como o botão de envio só aparece quando há texto no campo, essa etapa depende de uma ação manual do usuário para liberar o fluxo.
11. **Montagem e envio (loop)** — para cada item da planilha:
    - monta a mensagem (`backend/api/routes.py:50-55`);
    - `enviar_mensagem(pagina, mensagem)` preenche o campo, espera 3 segundos e clica no botão de enviar (`backend/whatsapp.py:46-58`);
    - `registrar_envio()` incrementa o contador (`backend/status.py:8-9`);
    - `time.sleep(intervalo * 60)` aguarda o intervalo configurado (`backend/api/routes.py:60`).
12. **Finalização** — ao terminar o loop, a rota retorna `{"status": "envios concluídos", "mensagens": <contador>}`.
13. **Atualização do painel** — em paralelo, o JavaScript consulta `GET /status` a cada 2 segundos e atualiza o elemento `#status` na tela (`front/static/js/painel.js:32-38`).

**Encerramento e erros:** o fluxo termina quando todas as linhas são processadas. Não há encerramento do navegador nem `try/except` no fluxo: se ocorrer um erro (planilha sem as colunas esperadas, arquivo inválido, falha no Playwright etc.), a exceção interrompe a requisição e o processo de envio, sem resposta de erro tratada nem feedback na interface.

---

## Exemplo prático de entrada e saída

Considere uma planilha fictícia com as colunas reais `PRODUTO`, `VALOR`, `CUPOM` e `LINK`:

| PRODUTO | VALOR | CUPOM | LINK |
| --- | --- | --- | --- |
| Fone Bluetooth | 129.90 | SOM10 | https://exemplo.com/produto |

O código monta a mensagem assim (`backend/api/routes.py:50-55`):

```python
mensagem = (
    f"🔥 {item['produto']}\n\n"
    f"💸 R$ {item['valor']:,.2f}\n"
    f"🎟️ Cupom: {item['cupom']}\n"
    f"{item['link']}"
)
```

Resultado final enviado no WhatsApp:

```text
🔥 Fone Bluetooth

💸 R$ 129,90
🎟️ Cupom: SOM10
https://exemplo.com/produto
```

Como cada campo é usado:

- `PRODUTO` → primeira linha, com o emoji `🔥`.
- `VALOR` → formatado com `R$` e a máscara `:,.2f` (duas casas decimais).
- `CUPOM` → linha com o prefixo `🎟️ Cupom:`.
- `LINK` → última linha, sem rótulo.

> **Os dados acima são fictícios** e servem apenas para ilustrar a transformação. O resultado também é ilustrativo.

A formatação do valor segue o padrão brasileiro: para `VALOR = 129.90` é exibido `R$ 129,90`; para `VALOR = 1500` seria exibido `R$ 1.500,00`.

---

## Arquitetura e organização dos arquivos

Árvore simplificada (arquivos relevantes):

```text
token-whatsapp/
├── backend/
│   ├── api/
│   │   ├── main.py        # Cria o app FastAPI, monta /static e inclui o router
│   │   └── routes.py      # Define as rotas e orquestra todo o fluxo de envio
│   ├── config.py          # Define BASE_DIR e PLANILHA (atualmente não utilizado)
│   ├── consumer.py        # Lê a planilha com Pandas e extrai as colunas
│   ├── status.py          # Contador de mensagens enviadas (em memória)
│   └── whatsapp.py        # Controle do WhatsApp Web via Playwright
├── front/
│   ├── index.html         # Estrutura do painel
│   └── static/
│       ├── css/style.css  # Estilo do painel
│       └── js/painel.js   # Upload, disparo da automação e polling do contador
├── session/               # Diretório vazio, não referenciado no código
├── uploads/               # Planilhas recebidas (criado em runtime)
├── Automacao-teste.xlsx   # Planilha de exemplo na raiz
├── requirements.txt       # Dependências
└── README.md              # Este documento
```

Responsabilidade de cada arquivo:

| Arquivo | Responsabilidade |
| --- | --- |
| `backend/api/main.py` | Ponto de entrada da aplicação. Instancia `FastAPI()`, monta o diretório `front/static` em `/static` e registra o `router`. |
| `backend/api/routes.py` | Define as rotas, recebe o upload, chama o processamento da planilha e orquestra abertura do WhatsApp, envio em loop e retorno do contador. |
| `backend/consumer.py` | `consumir_planilha()` lê o `.xlsx` e devolve a lista de itens (`produto`, `valor`, `cupom`, `link`). |
| `backend/whatsapp.py` | Funções de automação com Playwright: `abrir_whatsapp`, `conversa`, `preparar_mensagem`, `aguardar_gatilho`, `enviar_mensagem`. |
| `backend/status.py` | Guarda e atualiza `STATUS` (`zerar_contagem`, `registrar_envio`, `obter_contagem`). |
| `backend/config.py` | Define `BASE_DIR` e `PLANILHA`. **Não é importado em nenhum outro módulo** atualmente. |
| `front/index.html` | Painel com contador, campo de intervalo, upload e botão Iniciar. |
| `front/static/js/painel.js` | Exibe o nome do arquivo, envia o `FormData` para `/iniciar` e atualiza o contador via `/status`. |
| `front/static/css/style.css` | Estilização do painel. |

Funções presentes em `backend/whatsapp.py` que **não são chamadas** pelo fluxo atual: `preparar_mensagem` (definida em `backend/whatsapp.py:29`, usa `fill`). O import de `consumir_planilha` em `backend/whatsapp.py:1` também não é utilizado nesse arquivo.

---

## Rotas e comunicação entre frontend e backend

| Método | Rota | Parâmetros | Finalidade | Retorno |
| --- | --- | --- | --- | --- |
| GET | `/` | — | Serve o painel HTML (`front/index.html`). | Arquivo HTML |
| POST | `/iniciar` | `planilha` (arquivo, `multipart`), `intervalo` (inteiro, `Form`) | Salva a planilha, processa os dados e executa a automação de envio. | `{"status": "envios concluídos", "mensagens": <int>}` |
| GET | `/status` | — | Consulta o contador atual de mensagens enviadas. | `{"mensagens": <int>}` |
| GET | `/static/*` | — | Serve os arquivos estáticos (CSS e JS) montados por `StaticFiles`. | Arquivo estático |

Comunicação:

- **Envio**: o frontend usa `fetch("/iniciar", { method: "POST", body: formData })` com os campos `planilha` e `intervalo` (`front/static/js/painel.js:20-28`). O retorno dessa requisição **não é lido** pelo JavaScript.
- **Consulta de estado**: `setInterval` a cada 2000 ms faz `fetch("/status")` e escreve `dados.mensagens` no elemento de id `status` (`front/static/js/painel.js:32-38`).

---

## Como executar o projeto

Pré-requisitos:

- Python instalado (Python 3.13).
- Um ambiente com **interface gráfica**, pois o Playwright abre o navegador em modo visível (`headless=False`).

Passos (executando a partir da **raiz do projeto**, pois os caminhos `front/static` e `front/index.html` são relativos ao diretório de trabalho):

```powershell
# 1. Criar e ativar o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Instalar o navegador usado pelo Playwright
playwright install chromium

# 4. Iniciar a aplicação
uvicorn backend.api.main:app --reload
```

Depois, acessar `http://127.0.0.1:8000/` no navegador.

Observações:

- O ponto de entrada é `backend.api.main:app`.
- O login no WhatsApp Web é feito manualmente na janela do Chromium aberta pela automação.
- Não há variáveis de ambiente obrigatórias nem arquivo `.env` no projeto.

---

## Limitações e estado atual

**Funcionalidades implementadas:**

- Upload e processamento de planilha `.xlsx` pelas rotas `/` e `/iniciar`.
- Leitura das colunas `PRODUTO`, `VALOR`, `CUPOM`, `LINK`.
- Montagem da mensagem com emojis e formatação de valor.
- Automação do WhatsApp Web via Playwright (abertura, detecção da conversa, envio).
- Intervalo configurável em minutos.
- Contador de mensagens com atualização na interface por *polling*.

**Melhorias futuras ainda não implementadas** (não existem no código atual):

- Captura/exibição do QR Code diretamente no painel.
- Persistência da sessão em perfil dedicado.
- Tratamento de erros estruturado e validação da planilha.
- Encerramento adequado do navegador ao final do fluxo.
- Cronômetro real de "Tempo percorrido".

---

## Exemplo visual do resultado

Ao abrir o painel, o usuário vê um cartão escuro com:

- o título **"Painel"**;
- os indicadores **"Mensagens enviadas"** (começa em `0`) e **"Tempo percorrido"** (fixo em `00:00:00`);
- o campo **"Intervalo entre mensagens (minuto)"**;
- o botão **"Anexar planilha"**, que ao ser clicado revela o nome do arquivo selecionado;
- o botão azul **"Iniciar"**.

Fluxo de interação típico:

1. O usuário anexa a planilha e define o intervalo.
2. Clica em **Iniciar**; surge então a janela do Chromium com o WhatsApp Web.
3. O usuário faz o login e abre a conversa desejada.
4. A cada mensagem enviada, o número em **"Mensagens enviadas"** aumenta (atualizado a cada 2 segundos).
5. Na conversa do WhatsApp, as mensagens aparecem no formato ilustrado na seção *Exemplo prático de entrada e saída*.
