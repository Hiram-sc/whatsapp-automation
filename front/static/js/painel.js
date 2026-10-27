const inputFile = document.querySelector('#planilha');
const fileName = document.querySelector('.file-name');

inputFile.addEventListener('change', () => {
    if (inputFile.files.length > 0) {
        fileName.textContent = inputFile.files[0].name;
    } else {
        fileName.textContent = '';
    }
});

// Envia planilha e intervalo ao servidor através de uma requisição POST 
const botao = document.getElementById('iniciar');

botao.addEventListener("click", async () => {

    const arquivo = document.getElementById('planilha').files[0];
    const intervalo = document.getElementById('intervalo').value;

    const formData = new FormData();

    formData.append("planilha", arquivo);
    formData.append("intervalo", intervalo);

    await fetch("/iniciar", {
        method: "POST",
        body: formData
    });
});

// contador de mensagens
setInterval(async () => {
    const resposta = await fetch("/status");
    const dados = await resposta.json();

    document.getElementById("status").textContent =
        dados.mensagens;
}, 2000);


// modal qrcode
const botaoConectar = document.getElementById("conectar-whatsapp");
const modal = document.getElementById("modal-whatsapp");
const botaoFechar = document.getElementById("fechar-modal");
const qrCode = document.getElementById("qr-code");
const qrStatus = document.getElementById("qr-status");
const qrInstrucoes = document.getElementById("qr-instrucoes");

let modalAberto = false;
let tentativaQR = null;

function consultarQRCode() {
    if (!modalAberto) return;

    qrStatus.textContent = "Aguardando o QR Code...";
    qrCode.hidden = true;
    qrInstrucoes.hidden = true;

    // Evita reutilizar uma imagem antiga armazenada em cache.
    qrCode.src = `/whatsapp/qrcode?t=${Date.now()}`;
}

function abrirModal() {
    modalAberto = true;
    modal.hidden = false;

    qrStatus.textContent = "Iniciando conexão com o WhatsApp...";

    consultarQRCode();
}

function fecharModal() {
    modalAberto = false;
    modal.hidden = true;

    qrCode.removeAttribute("src");
    qrCode.hidden = true;

    clearTimeout(tentativaQR);
}

qrCode.addEventListener("load", () => {
    if (!modalAberto) return;

    clearTimeout(tentativaQR);

    qrStatus.textContent = "Escaneie o QR Code com seu celular.";
    qrCode.hidden = false;
    qrInstrucoes.hidden = false;
});

qrCode.addEventListener("error", () => {
    if (!modalAberto) return;

    qrStatus.textContent =
        "Carregando o WhatsApp... tentando novamente.";

    clearTimeout(tentativaQR);

    tentativaQR = setTimeout(consultarQRCode, 2000);
});

function exibirSucessoSessao() {
    if (!modalAberto) return;

    clearTimeout(tentativaQR);

    qrStatus.textContent = "Whatsapp aberto com sucesso!";
    qrCode.hidden = true;
    qrInstrucoes.hidden = true;
}

function exibirSessaoAtiva() {
    if (!modalAberto) return;

    clearTimeout(tentativaQR);

    qrStatus.textContent = "Seu whatsapp já está conectado!";
    qrCode.hidden = true;
    qrInstrucoes.hidden = true;
}

botaoConectar.addEventListener("click", abrirModal);
botaoFechar.addEventListener("click", fecharModal);

// Fecha o modal ao clicar fora do conteúdo.
modal.addEventListener("click", (evento) => {
    if (evento.target === modal) {
        fecharModal();
    }
});

// Fecha o modal com a tecla Esc.
document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && modalAberto) {
        fecharModal();
    }
});
