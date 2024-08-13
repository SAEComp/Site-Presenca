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
        document.getElementById('message').innerText = 'Erro ao acessar a câmera: ' + err.message;
    }
}

startCamera();