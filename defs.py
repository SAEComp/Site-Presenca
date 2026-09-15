import datetime
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def copiarformatacaodepresenca(service, spreadsheet_id, source_sheet_id, target_sheet_id):
    source_sheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[],
        fields="sheets.conditionalFormats"
    ).execute()['sheets'][source_sheet_id].get('conditionalFormats', [])

    for rule in source_sheet:
        for range_ in rule['ranges']:
            range_['sheetId'] = target_sheet_id

    requests = [{
        'addConditionalFormatRule': {
            'rule': rule,
            'index': 0
        }
    } for rule in source_sheet]

    if requests:
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

def copiarformatacao(service, spreadsheet_id, source_sheet_id, target_sheet_id):
    source_sheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[],
        fields="sheets.data.rowData.values.userEnteredFormat,sheets.data.rowData.values.effectiveFormat"
    ).execute()['sheets'][source_sheet_id].get('data', [])[0].get('rowData', [])

    requests = []
    for row_index, row in enumerate(source_sheet):
        for col_index, cell in enumerate(row.get('values', [])):
            if 'userEnteredFormat' in cell:
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': target_sheet_id,
                            'startRowIndex': row_index,
                            'endRowIndex': row_index + 1,
                            'startColumnIndex': col_index,
                            'endColumnIndex': col_index + 1
                        },
                        'cell': {
                            'userEnteredFormat': cell['userEnteredFormat']
                        },
                        'fields': 'userEnteredFormat'
                    }
                })

    if requests:
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

def copiarlarguradecoluna(service, spreadsheet_id, source_sheet_id, target_sheet_id):
    source_sheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[],
        fields="sheets.data.columnMetadata"
    ).execute()['sheets'][source_sheet_id].get('data', [])[0].get('columnMetadata', [])

    requests = []
    for col_index, col in enumerate(source_sheet):
        if 'pixelSize' in col:
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': target_sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': col_index,
                        'endIndex': col_index + 1
                    },
                    'properties': {
                        'pixelSize': col['pixelSize']
                    },
                    'fields': 'pixelSize'
                }
            })

    if requests:
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        
        
#função que atualiza a planilha do sheets. Executada todo dia meia noite somente se o arquivo 'codes.txt' não estiver vazio e limpa ele após executar

def diariamente():
    print("--- Iniciando Processo de Sincronização ---")
    
    if is_file_empty('codes.txt'):
        print("Aviso: Arquivo 'codes.txt' está vazio. Encerrando.")
        return

    # 1. Autenticação (Mantém igual)
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = '1aYOqH2rB6iRCJJBv4DRS6Ni0TBaYiHi7epVVOxieQgQ'
    sheet = service.spreadsheets()

    # 2. Identificar a aba de hoje
    current_date = datetime.datetime.now().strftime("%d/%B/%Y")
    target_sheet_title = f"Sheet_{current_date.replace('/', '_')}"
    print(f"Data de hoje: {current_date} | Aba alvo: {target_sheet_title}")

    # 3. Verificar se a aba de hoje já existe
    metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
    existing_sheets = [s['properties']['title'] for s in metadata.get('sheets', [])]
    
    if target_sheet_title not in existing_sheets:
        print(f"Aba {target_sheet_title} não encontrada. Criando agora...")
        
        # Criar a nova aba
        sheet.batchUpdate(spreadsheetId=spreadsheet_id, body={
            'requests': [{'addSheet': {'properties': {'title': target_sheet_title}}}]
        }).execute()

        # Copiar dados da Sheet1 (Template) para a nova aba
        # IMPORTANTE: Verifique se sua aba molde se chama 'Sheet1'
        template_data = sheet.values().get(spreadsheetId=spreadsheet_id, range='Sheet1!A:B').execute().get('values', [])
        
        if template_data:
            # 1. Cola Nomes e IDs
            sheet.values().update(spreadsheetId=spreadsheet_id, range=f"{target_sheet_title}!A1",
                                  valueInputOption="RAW", body={"values": template_data}).execute()
            
            # 2. Preenche "Ausente" na coluna C para todos
            num_rows = len(template_data)
            absence = [["Ausente"] for _ in range(1, num_rows)]
            sheet.values().update(spreadsheetId=spreadsheet_id, range=f"{target_sheet_title}!C2:C{num_rows}",
                                  valueInputOption="RAW", body={"values": absence}).execute()
            
            # 3. Coloca a data em E2
            sheet.values().update(spreadsheetId=spreadsheet_id, range=f"{target_sheet_title}!E2",
                                  valueInputOption="RAW", body={"values": [[current_date]]}).execute()
        
        print(f"Aba {target_sheet_title} criada com sucesso! Rode o script novamente para marcar as presenças.")
        return # Encerra aqui para dar tempo do Google processar a nova aba

    # 4. MARCAR PRESENÇA (Só roda se a aba já existir)
    print(f"Aba {target_sheet_title} confirmada. Lendo dados...")
    
    with open('codes.txt', 'r') as file:
        presentes_ids = [line.strip() for line in file if line.strip()]

    # Pega os dados da aba de HOJE
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=f"{target_sheet_title}!A:C").execute()
    values = result.get('values', [])

    encontrados = 0
    for i, row in enumerate(values):
        if len(row) < 2 or i == 0: continue
        
        id_planilha = str(row[1]).strip()
        if id_planilha in presentes_ids:
            print(f"-> Marcando Presente para: {id_planilha}")
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{target_sheet_title}!C{i + 1}',
                valueInputOption="RAW",
                body={"values": [["Presente"]]}
            ).execute()
            encontrados += 1

    if encontrados > 0:
        clear_file('codes.txt')
        print(f"Sincronização concluída! {encontrados} pessoas com presença.")
    else:
        print("Nenhum ID do arquivo codes.txt foi encontrado nesta planilha.")

def is_file_empty(file_path):
    try:
        with open(file_path, 'r') as file:
            # Lê o primeiro caractere e verifica se o arquivo está vazio
            first_char = file.read(1)
            if not first_char:
                return True  # Arquivo está vazio
            return False  # Arquivo não está vazio
    except FileNotFoundError:
        print("O arquivo não foi encontrado.")
        return False
    
def clear_file(file_path):
    with open(file_path, 'w') as file:
        pass
