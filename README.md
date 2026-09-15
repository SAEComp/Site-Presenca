# 📋 Sistema de Presença - SAEComp

Sistema de gerenciamento e marcação de presença via leitor de código de barras/QR Code, integrado automaticamente com o **Google Sheets**. O projeto realiza a leitura dos cartões USP dos membros, gera a aba do dia na planilha e marca a presença dos usuários presentes.

---

## 🛠️ Pré-requisitos

Antes de começar, certifique-se de ter os seguintes itens instalados no seu sistema:

* **Python 3.10+**
* Navegador **Google Chrome** ou equivalente
* Câmera/Webcam configurada na máquina

---

## 🚀 Como Rodar o Projeto

### 1. Clonar o Repositório e Criar o Ambiente Virtual

Abra o terminal na pasta onde deseja salvar o projeto e execute:

```bash
# Clone o repositório
git clone git@github.com:SAEComp/Site-Presenca.git
cd Site-Presenca

# Crie e ative o ambiente virtual (venv)
python3 -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate

```

### 2. Instalar as Dependências

Com o ambiente virtual ativo, instale os pacotes necessários especificados no `requirements.txt`:

```bash
pip install -r requirements.txt

```

---

## 🔑 Autenticação e Configuração do Google Sheets

O sistema sincroniza a lista de presença diretamente com uma planilha no Google Drive.

* 📊 **Link da Planilha:** [Acessar Planilha de Presença](https://docs.google.com/spreadsheets/d/1aYOqH2rB6iRCJJBv4DRS6Ni0TBaYiHi7epVVOxieQgQ)

### 🔑 Configuração das Credenciais do Google Cloud

Para que o sistema consiga se comunicar com a API do Google Sheets, você precisará do arquivo de credenciais `client_secret.json`:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie ou selecione o seu projeto e ative a **Google Sheets API**.
3. Vá em **Início de sessão e segurança / Credenciais** (OAuth 2.0 Client IDs).
4. Faça o download do arquivo de chaves de acesso, renomeie-o para `client_secret.json` e **cole na raiz do projeto**.

---

### 🌐 Gerando o arquivo `token.json` (Primeiro Acesso)

Depois de colocar o `client_secret.json` na raiz:

1. Na primeira vez em que você executar o script de sincronização (`python enviar_presenca.py`), **uma janela do navegador será aberta automaticamente**.
2. Faça login com a conta do Google que possui permissão de edição na planilha.
3. Caso apareça a mensagem *"O Google não verificou este app"*, clique em **Avançado** e depois em **Acessar (não seguro)**.
4. Conceda as permissões solicitadas.
5. Após a validação, o arquivo **`token.json` será gerado automaticamente** pelo Python na raiz do projeto.

---

## 💻 Executando o Sistema

### 1. Iniciar o Dashboard de Leitura (Flask Web App)

Rode o aplicativo para abrir o scanner da câmera:

```bash
python app.py

```

Acesse no seu navegador:

* **Localmente:** `http://localhost:5000/dashboard`
* **Em outro dispositivo na mesma rede:** `http://<IP-DA-MAQUINA>:5000/dashboard` *(Caso use IP externo, é necessário habilitar a exceção de câmera no `chrome://flags`)*.

### 2. Sincronizar com o Google Sheets

Para enviar as presenças capturadas para a planilha e gerar a aba do dia:

```bash
python enviar_presenca.py

```

---

## ⚠️ Solução de Problemas Rápidos

* **Câmera não abre (`getUserMedia undefined`):** O navegador exige conexão HTTPS ou acesso via `http://localhost:5000`. Se acessar via IP local em outro dispositivo, configure a flag `chrome://flags/#unsafely-treat-insecure-origin-as-secure`.
* **Erro `invalid_grant` no Google:** O token de acesso expirou. Remova o arquivo com `rm token.json` e rode `python enviar_presenca.py` novamente para refazer o login no navegador.

