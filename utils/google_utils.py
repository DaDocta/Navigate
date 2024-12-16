import io
import zipfile
from lxml import etree
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

from utils.general_utils import search_in_word_content, search_in_excel_content

def authenticate_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service

def download_file(service, file_id, mime_type):
    try:
        if mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            request = service.files().get_media(fileId=file_id)
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh
    except Exception as e:
        print(f"Error downloading file {file_id}: {e}")
        return None

def export_google_doc_as_text(service, file_id):
    try:
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error exporting Google Doc {file_id}: {e}")
        return ''

def search_google_drive(service, search_term, ai_prompt=False):
    query = ("mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or "
             "mimeType='application/vnd.google-apps.document' or name contains '.docx' or "
             "mimeType='application/vnd.google-apps.spreadsheet' or name contains '.xlsx'")

    results = service.files().list(q=query, pageSize=100, fields="files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
        return []

    search_results = []
    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']

        if file_name.startswith('~$'):
            continue

        fh = download_file(service, file_id, mime_type)
        if fh:
            if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_name.endswith('.docx'):
                search_results.extend(search_in_word_content(fh, search_term, file_name))
            elif mime_type == 'application/vnd.google-apps.document':
                doc_text = export_google_doc_as_text(service, file_id)
                if doc_text and search_term.lower() in doc_text.lower():
                    search_results.append((file_name, f"Contains search term '{search_term}'"))
            elif mime_type == 'application/vnd.google-apps.spreadsheet' or file_name.endswith('.xlsx'):
                search_results.extend(search_in_excel_content(fh, search_term, file_name))

    print(f"Found {len(search_results)} results.")
    return search_results
