const inputFile = document.querySelector('#planilha');
const fileName = document.querySelector('.file-name');

inputFile.addEventListener('change', () => {
    if (inputFile.files.length > 0) {
        fileName.textContent = inputFile.files[0].name;
    } else {
        fileName.textContent = '';
    }
});

/* transformar em metodo POST */
const botao = document.getElementById('iniciar');

botao.addEventListener("click", async () => {

    const arquivo = document.getElementById('planilha').files[0];

    const formData = new FormData();
    formData.append("planilha", arquivo);

    await fetch("/iniciar", {
        method: "POST",
        body: formData
    });
});