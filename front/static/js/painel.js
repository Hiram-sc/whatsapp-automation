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
}, 5000);
