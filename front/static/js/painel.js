
const inputFile = document.querySelector('#planilha');
const fileName = document.querySelector('.file-name');

inputFile.addEventListener('change', () => {
    if (inputFile.files.length > 0) {
        fileName.textContent = inputFile.files[0].name;
    } else {
        fileName.textContent = 'Nenhum arquivo selecionado';
    }
});

// Envio da automação
const botao = document.getElementById('iniciar');

botao.addEventListener('click', async () => {
    const arquivo = document.getElementById('planilha').files[0];
    const intervalo = document.getElementById('intervalo').value;
    const nomeGrupo = document.getElementById('nome-grupo').value;

    const formData = new FormData();

    formData.append('planilha', arquivo);
    formData.append('intervalo', intervalo);
    formData.append('nome_grupo', nomeGrupo);

    try {
        botao.disabled = true;
        botao.textContent = 'Iniciando...';

        const resposta = await fetch('/iniciar', {
            method: 'POST',
            body: formData
        });

        if (!resposta.ok) {
            const erro = await resposta.json();
            throw new Error(erro.detail || 'Não foi possível iniciar a automação.');
        }

    } catch (erro) {
        console.error('Erro ao iniciar automação:', erro);
        alert(erro.message);

    } finally {
        botao.disabled = false;
        botao.innerHTML = `
            Iniciar automação
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="m9 5 10 7-10 7V5Z" fill="currentColor"/>
            </svg>
        `;
    }
});

// Contador de mensagens
setInterval(async () => {
    try {
        const resposta = await fetch('/status');

        if (!resposta.ok) return;

        const dados = await resposta.json();

        document.getElementById('status').textContent =
            dados.mensagens;

    } catch (erro) {
        console.error('Erro ao consultar contador:', erro);
    }
}, 2000);


// Modal do QR Code
const botaoConectar = document.getElementById('conectar-whatsapp');
const modal = document.getElementById('modal-whatsapp');
const botaoFechar = document.getElementById('fechar-modal');
const qrCode = document.getElementById('qr-code');
const qrStatus = document.getElementById('qr-status');
const qrInstrucoes = document.getElementById('qr-instrucoes');
const qrPlaceholder = document.getElementById('qr-placeholder');

let modalAberto = false;
let tentativaQR = null;

function consultarQRCode() {
    if (!modalAberto) return;

    qrStatus.textContent = 'Aguardando o QR Code...';
    qrCode.hidden = true;
    qrPlaceholder.hidden = false;
    qrInstrucoes.hidden = true;

    // Evita reutilizar uma imagem antiga armazenada em cache.
    qrCode.src = `/whatsapp/qrcode?t=${Date.now()}`;
}

function abrirModal() {
    modalAberto = true;
    modal.hidden = false;

    qrStatus.textContent = 'Iniciando conexão com o WhatsApp...';

    consultarQRCode();
}

function fecharModal() {
    modalAberto = false;
    modal.hidden = true;

    qrCode.removeAttribute('src');
    qrCode.hidden = true;
    qrPlaceholder.hidden = false;

    clearTimeout(tentativaQR);
}

qrCode.addEventListener('load', () => {
    if (!modalAberto) return;

    clearTimeout(tentativaQR);

    qrStatus.textContent = 'Escaneie o QR Code com seu celular.';
    qrCode.hidden = false;
    qrPlaceholder.hidden = true;
    qrInstrucoes.hidden = false;
});

qrCode.addEventListener('error', () => {
    if (!modalAberto) return;

    qrStatus.textContent = 'Carregando o WhatsApp... tentando novamente.';

    qrCode.hidden = true;
    qrPlaceholder.hidden = false;

    clearTimeout(tentativaQR);

    tentativaQR = setTimeout(consultarQRCode, 2000);
});

function exibirSucessoSessao() {
    if (!modalAberto) return;

    clearTimeout(tentativaQR);

    qrStatus.textContent = 'WhatsApp aberto com sucesso!';
    qrCode.hidden = true;
    qrPlaceholder.hidden = true;
    qrInstrucoes.hidden = true;
}

function exibirSessaoAtiva() {
    if (!modalAberto) return;

    clearTimeout(tentativaQR);

    qrStatus.textContent = 'Seu WhatsApp já está conectado!';
    qrCode.hidden = true;
    qrPlaceholder.hidden = true;
    qrInstrucoes.hidden = true;
}

botaoConectar.addEventListener('click', abrirModal);
botaoFechar.addEventListener('click', fecharModal);

// Fecha o modal ao clicar fora do conteúdo.
modal.addEventListener('click', (evento) => {
    if (evento.target === modal) {
        fecharModal();
    }
});

// Fecha o modal com a tecla Esc.
document.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && modalAberto) {
        fecharModal();
    }
});
