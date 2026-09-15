async function startCamera() {
    const video = document.getElementById('camera');
    const codeReader = new ZXing.BrowserMultiFormatReader();

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        video.srcObject = stream;

        codeReader.decodeFromVideoDevice(null, 'camera', async (result, error) => {
            if (result) {
                console.log(result.text, 'presente!');
                document.getElementById('message').innerText = `${result.text} presente`;
                
                try {
                    await fetch('/save_code', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ code: result.text }),
                    });
                } catch (err) {
                    console.error('Erro ao enviar código para o servidor:', err);
                }
            }
            if (error) {
                console.error('Erro na leitura do código:', error);
            }
        });
    } catch (err) {
        console.error('Erro ao acessar a câmera:', err);
        let mensagem = 'Erro ao acessar a câmera: ';
        
        if (err.name === 'NotAllowedError') {
            mensagem += 'Permissão negada. Clique no 🔒 na barra de URL e permita o acesso à câmera.';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
            mensagem += 'Câmera não encontrada no dispositivo.';
        } else if (err.name === 'NotSupportedError') {
            mensagem += 'Seu navegador não suporta acesso à câmera.';
        } else if (err.name === 'SecurityError') {
            mensagem += 'Use HTTPS ou acesse via localhost.';
        } else {
            mensagem += err.message;
        }
        
        document.getElementById('message').innerText = mensagem;
    }
}

startCamera();