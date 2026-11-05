// DOM Elements
const inputFile = document.querySelector('#planilha');
const fileName = document.querySelector('.file-name');
const botaoIniciar = document.getElementById('iniciar');
const campoIntervalo = document.getElementById('intervalo');
const campoGrupo = document.getElementById('nome-grupo');
const contador = document.getElementById('status');
const statDescription = document.getElementById('stat-description');
const feedback = document.getElementById('form-feedback');

const connectionIndicator = document.getElementById('connection-indicator');
const connectionLabel = document.getElementById('connection-label');

const botaoConectar = document.getElementById('conectar-whatsapp');
const modal = document.getElementById('modal-whatsapp');
const botaoFechar = document.getElementById('fechar-modal');
const qrCode = document.getElementById('qr-code');
const qrStatus = document.getElementById('qr-status');
const qrInstrucoes = document.getElementById('qr-instrucoes');
const qrPlaceholder = document.getElementById('qr-placeholder');
const qrPlaceholderText = document.getElementById('qr-placeholder-text');
// Constants

const CONTEUDO_BOTAO_INICIAR = `
    Iniciar automação
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="m9 5 10 7-10 7V5Z" fill="currentColor"/>
    </svg>
`;

const ROTULOS_CONEXAO = {
    desconectado: 'OFF-LINE',
    conectando: 'CONECTANDO',
    aguardando_qr: 'AGUARDANDO QR',
    conectado: 'AO VIVO',
    erro: 'ERRO',
};

const INTERVALO_MINIMO = 1;
const INTERVALO_MAXIMO = 1440;
const STATUS_TIMEOUT_MS = 8000;
const INICIAR_TIMEOUT_MS = 90000;
const QR_TIMEOUT_MS = 90000;
const QR_RETRY_MS = 2000;
// State

let estadoAtual = {
    conexao: 'desconectado',
    automacao: 'ociosa',
    mensagens_enviadas: 0,
    total: 0,
    automacao_detalhe: null,
};

let modalAberto = false;
let statusTimer = null;
let qrRetryTimer = null;
let qrObjectUrl = null;
let qrRequestId = 0;
let ultimoEstadoAutomacao = 'ociosa';
let falhasStatus = 0;
let iniciandoEnvio = false;
// Helpers

// Verifica se há automação em andamento.
function automacaoAtiva() {
    return ['iniciando', 'em_execucao'].includes(estadoAtual.automacao);
}

// Exibe uma mensagem de feedback no formulário.
function mostrarFeedback(mensagem, tipo = 'error') {
    feedback.textContent = mensagem;
    feedback.className = `form-feedback ${tipo}`;
    feedback.hidden = false;
}

// Oculta o feedback do formulário.
function limparFeedback() {
    feedback.hidden = true;
    feedback.textContent = '';
    feedback.className = 'form-feedback';
}

// Executa uma requisição com timeout e tratamento de erros.
async function requisitar(url, opcoes = {}, timeoutMs = 15000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const resposta = await fetch(url, {
            ...opcoes,
            signal: controller.signal,
            cache: 'no-store',
        });

        const tipoConteudo = resposta.headers.get('content-type') || '';
        const corpo = tipoConteudo.includes('application/json')
            ? await resposta.json().catch(() => null)
            : null;

        if (!resposta.ok) {
            let detalhe = corpo?.detail;

            if (detalhe && typeof detalhe !== 'string') {
                detalhe = 'Dados inválidos. Confira os campos e tente novamente.';
            }

            const erro = new Error(
                detalhe || `Erro HTTP ${resposta.status}.`
            );
            erro.status = resposta.status;
            throw erro;
        }

        return { resposta, corpo };
    } catch (erro) {
        if (erro.name === 'AbortError') {
            throw new Error('Tempo esgotado ao consultar o servidor.');
        }

        if (erro instanceof TypeError) {
            throw new Error('Não foi possível conectar ao servidor.');
        }

        throw erro;
    } finally {
        clearTimeout(timer);
    }
}
// Status

// Atualiza o indicador visual de conexão.
function atualizarIndicadorConexao() {
    const conectado = estadoAtual.conexao === 'conectado';

    connectionIndicator.classList.toggle('success', conectado);
    connectionIndicator.classList.toggle('offline', !conectado);
    connectionLabel.textContent =
        ROTULOS_CONEXAO[estadoAtual.conexao] || estadoAtual.conexao;
}

// Gera a descrição do estado da automação.
function descricaoAutomacao(enviadas) {
    const total = Number(estadoAtual.total) || 0;

    if (estadoAtual.automacao === 'iniciando') {
        return 'Iniciando automação...';
    }

    if (estadoAtual.automacao === 'em_execucao') {
        return `Em execução · ${enviadas} / ${total}`;
    }

    if (estadoAtual.automacao === 'finalizada') {
        return `Finalizada · ${enviadas} / ${total}`;
    }

    if (estadoAtual.automacao === 'erro') {
        return 'Erro na automação';
    }

    return 'Total de mensagens processadas';
}

// Atualiza o botão, a descrição e o feedback da automação.
function atualizarAutomacao(enviadas) {
    const estado = estadoAtual.automacao;
    const ativa = automacaoAtiva();

    statDescription.textContent = iniciandoEnvio
        ? 'Iniciando automação...'
        : descricaoAutomacao(enviadas);

    botaoIniciar.disabled =
        iniciandoEnvio || estadoAtual.conexao !== 'conectado' || ativa;

    if (iniciandoEnvio) {
        botaoIniciar.textContent = 'Iniciando...';
    } else if (ativa) {
        botaoIniciar.textContent = 'Automação em execução...';
    } else {
        botaoIniciar.innerHTML = CONTEUDO_BOTAO_INICIAR;
    }

    if (estado !== ultimoEstadoAutomacao) {
        if (estado === 'finalizada') {
            mostrarFeedback(
                `Automação concluída: ${enviadas} mensagem(ns) enviada(s).`,
                'success'
            );
        } else if (estado === 'erro') {
            mostrarFeedback(
                estadoAtual.automacao_detalhe || 'A automação falhou.',
                'error'
            );
        }

        ultimoEstadoAutomacao = estado;
    }
}

// Renderiza o estado atual na interface.
function renderizarEstado() {
    const enviadas = Number(estadoAtual.mensagens_enviadas ?? 0);

    contador.textContent = enviadas;
    atualizarIndicadorConexao();
    atualizarAutomacao(enviadas);

    if (modalAberto && estadoAtual.conexao === 'conectado') {
        exibirSessaoAtiva();
    }
}

// Consulta o status do backend e atualiza a interface.
async function atualizarStatus() {
    try {
        const { corpo } = await requisitar('/status', {}, STATUS_TIMEOUT_MS);

        estadoAtual = {
            conexao: corpo?.conexao || 'desconectado',
            automacao: corpo?.automacao || 'ociosa',
            automacao_detalhe: corpo?.automacao_detalhe || null,
            total: Number(corpo?.total ?? 0),
            mensagens_enviadas: Number(corpo?.mensagens_enviadas ?? 0),
        };

        falhasStatus = 0;
        renderizarEstado();
    } catch (erro) {
        falhasStatus += 1;
        connectionIndicator.classList.remove('success');
        connectionIndicator.classList.add('offline');
        connectionLabel.textContent = 'SEM CONEXÃO';
        statDescription.textContent = 'Servidor indisponível';
        botaoIniciar.disabled = true;

        if (falhasStatus === 1) {
            console.error('Erro ao consultar o status:', erro);
        }
    }
}

// Agenda a atualização periódica do status.
async function cicloStatus() {
    await atualizarStatus();

    clearTimeout(statusTimer);
    statusTimer = setTimeout(cicloStatus, 2000);
}
// QR Code

// Exibe um texto no lugar do QR Code.
function definirPlaceholderQr(texto) {
    qrPlaceholderText.textContent = texto;
    qrCode.hidden = true;
    qrPlaceholder.hidden = false;
    qrInstrucoes.hidden = true;
}

// Libera a URL temporária do QR Code.
function limparUrlQr() {
    if (qrObjectUrl) {
        URL.revokeObjectURL(qrObjectUrl);
        qrObjectUrl = null;
    }
}

// Cancela novas tentativas de carregar o QR Code.
function pararRetryQr() {
    clearTimeout(qrRetryTimer);
    qrRetryTimer = null;
    qrRequestId += 1;
}

// Agenda uma nova tentativa de carregar o QR Code.
function agendarRetryQr() {
    if (!modalAberto) return;

    clearTimeout(qrRetryTimer);
    qrStatus.textContent = 'Aguardando o WhatsApp... Nova tentativa em 2s.';
    qrRetryTimer = setTimeout(consultarQRCode, QR_RETRY_MS);
}

// Indica que o WhatsApp já está conectado.
function exibirSessaoAtiva() {
    if (!modalAberto) return;

    pararRetryQr();
    limparUrlQr();

    qrCode.hidden = true;
    qrCode.removeAttribute('src');
    qrPlaceholder.hidden = true;
    qrInstrucoes.hidden = true;
    qrStatus.textContent = 'Seu WhatsApp já está conectado!';
}

// Busca e exibe o QR Code de conexão.
async function consultarQRCode() {
    if (!modalAberto) return;

    const requestId = ++qrRequestId;

    clearTimeout(qrRetryTimer);
    qrRetryTimer = null;
    definirPlaceholderQr('Carregando o QR Code...');
    qrStatus.textContent = 'Carregando o QR Code...';

    try {
        const { resposta } = await requisitar(
            `/whatsapp/qrcode?t=${Date.now()}`,
            {},
            QR_TIMEOUT_MS
        );

        if (!modalAberto || requestId !== qrRequestId) return;

        const imagem = await resposta.blob();

        if (!modalAberto || requestId !== qrRequestId) return;

        limparUrlQr();
        qrObjectUrl = URL.createObjectURL(imagem);
        qrCode.src = qrObjectUrl;
        qrCode.hidden = false;
        qrPlaceholder.hidden = true;
        qrInstrucoes.hidden = false;
        qrStatus.textContent = 'Escaneie o QR Code com seu celular.';
    } catch (erro) {
        if (!modalAberto || requestId !== qrRequestId) return;

        if (erro.status === 409) {
            exibirSessaoAtiva();
            return;
        }

        if (erro.status === 503) {
            qrStatus.textContent = erro.message;
            agendarRetryQr();
            return;
        }

        console.error('Erro ao carregar o QR Code:', erro);
        definirPlaceholderQr('Não foi possível carregar o QR Code.');
        qrStatus.textContent =
            erro.message || 'Não foi possível carregar o QR Code.';
    }
}
// Modal

// Abre o modal de conexão e inicia as consultas.
function abrirModal() {
    modalAberto = true;
    modal.hidden = false;

    consultarQRCode();
    atualizarStatus();
}

// Fecha o modal e limpa os recursos do QR Code.
function fecharModal() {
    modalAberto = false;
    modal.hidden = true;

    pararRetryQr();
    limparUrlQr();

    qrCode.removeAttribute('src');
    qrCode.hidden = true;
    qrPlaceholder.hidden = false;
    qrInstrucoes.hidden = true;
    qrPlaceholderText.textContent = 'Aguardando QR Code...';
}
// Events

// Valida o arquivo selecionado.
inputFile.addEventListener('change', () => {
    limparFeedback();

    if (inputFile.files.length === 0) {
        fileName.textContent = 'Nenhum arquivo selecionado';
        return;
    }

    const arquivo = inputFile.files[0];

    if (!arquivo.name.toLowerCase().endsWith('.xlsx')) {
        inputFile.value = '';
        fileName.textContent = 'Nenhum arquivo selecionado';
        mostrarFeedback('Envie uma planilha no formato .xlsx.', 'error');
        return;
    }

    fileName.textContent = arquivo.name;
});

// Valida o formulário e inicia a automação.
botaoIniciar.addEventListener('click', async () => {
    limparFeedback();

    const arquivo = inputFile.files[0];
    const intervalo = Number(campoIntervalo.value);
    const nomeGrupo = campoGrupo.value.trim();

    if (!arquivo) {
        mostrarFeedback('Selecione uma planilha no formato .xlsx.', 'error');
        return;
    }

    if (!arquivo.name.toLowerCase().endsWith('.xlsx')) {
        mostrarFeedback('Envie uma planilha no formato .xlsx.', 'error');
        return;
    }

    if (!nomeGrupo) {
        mostrarFeedback('Informe o nome do grupo.', 'error');
        return;
    }

    if (
        !Number.isFinite(intervalo) ||
        intervalo < INTERVALO_MINIMO ||
        intervalo > INTERVALO_MAXIMO
    ) {
        mostrarFeedback(
            `O intervalo deve estar entre ${INTERVALO_MINIMO} e ${INTERVALO_MAXIMO} minutos.`,
            'error'
        );
        return;
    }

    if (estadoAtual.conexao !== 'conectado') {
        mostrarFeedback(
            'Conecte o WhatsApp antes de iniciar a automação.',
            'error'
        );
        return;
    }

    if (automacaoAtiva()) {
        mostrarFeedback('Já existe uma automação em andamento.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('planilha', arquivo);
    formData.append('intervalo', String(intervalo));
    formData.append('nome_grupo', nomeGrupo);

    iniciandoEnvio = true;
    botaoIniciar.disabled = true;
    botaoIniciar.textContent = 'Iniciando...';

    try {
        const { corpo } = await requisitar(
            '/iniciar',
            {
                method: 'POST',
                body: formData,
            },
            INICIAR_TIMEOUT_MS
        );

        mostrarFeedback(
            `Automação iniciada para ${corpo?.total ?? 0} mensagem(ns).`,
            'success'
        );
    } catch (erro) {
        mostrarFeedback(erro.message, 'error');
    } finally {
        iniciandoEnvio = false;
        await atualizarStatus();
    }
});

botaoConectar.addEventListener('click', abrirModal);
botaoFechar.addEventListener('click', fecharModal);

modal.addEventListener('click', (evento) => {
    if (evento.target === modal) {
        fecharModal();
    }
});

document.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && modalAberto) {
        fecharModal();
    }
});
// Start

cicloStatus();
