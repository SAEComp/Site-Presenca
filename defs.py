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

#função que atualiza a planilha do sheets. Executada todo dia meia noite somente se o arquivo 'codes.txt' não estiver vazio e limpa ele após executar
def diariamente():
    if not is_file_empty('codes.txt'):
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
        spreadsheet_id = '17HqMNAT7WVbt9FsrtNz-7SfFIejBsLL9yZq7ysHFUhQ'
        range_name = 'Sheet1!E2'
        sheet = service.spreadsheets()

        # Verificar a data atual
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        current_date = datetime.datetime.now().strftime("%d/%B/%Y")

        # Se a data da planilha for diferente da data atual, criar uma nova aba
        if not values or values[0][0] != current_date:
            new_sheet_title = f"Sheet_{current_date.replace('/', '_')}"
            sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', '')

            # Criar nova aba
            new_sheet = {
                'properties': {
                    'title': new_sheet_title
                }
            }
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'requests': [
                        {'addSheet': new_sheet}
                    ]
                }
            ).execute()

            new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
            original_sheet_id = sheet_metadata['sheets'][0]['properties']['sheetId']

            # Copiar dados da aba original para a nova aba
            source_range = 'Sheet1!A:E'
            source_values = sheet.values().get(spreadsheetId=spreadsheet_id, range=source_range).execute().get('values', [])

            if source_values:
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{new_sheet_title}!A1",
                    valueInputOption="RAW",
                    body={"values": source_values}
                ).execute()

            # Marcar todos como ausentes na nova aba
            row_count = len(source_values)
            absence_values = [["Ausente"] for _ in range(1, row_count)]
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{new_sheet_title}!C2:C{row_count}",
                valueInputOption="RAW",
                body={"values": absence_values}
            ).execute()

            # Atualizar a data na nova aba
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{new_sheet_title}!E2",
                valueInputOption="RAW",
                body={"values": [[current_date]]}
            ).execute()

            # Copiar formatação condicional
            copiarformatacaodepresenca(service, spreadsheet_id, original_sheet_id, new_sheet_id)

            # Copiar formatação de células
            copiarformatacao(service, spreadsheet_id, original_sheet_id, new_sheet_id)

            # Copiar tamanhos das colunas
            copiarlarguradecoluna(service, spreadsheet_id, original_sheet_id, new_sheet_id)

            range_name = f"{new_sheet_title}!B:B"
        else:
            range_name = 'Sheet1!B:B'

        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        data = current_date
        with open('codes.txt', 'r') as file:
            for line in file:
                code = int(line.strip())
                for i, row in enumerate(values):
                    if row and row[0] != 'NUsp' and int(row[0]) == code:
                        cell_range = f'{new_sheet_title}!C{i + 1}'  
                        receber = [["Presente"]]
                        update_result = sheet.values().update(
                            spreadsheetId=spreadsheet_id,
                            range=cell_range,
                            valueInputOption="RAW",
                            body={"values": receber}).execute()
                        nome_range = f'{new_sheet_title}!A{i + 1}'
                        nome_result = sheet.values().get(spreadsheetId=spreadsheet_id, range=nome_range).execute()
        clear_file('codes.txt')
    else:
        return