import os
import json
import httpx
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

class GoogleDriveClient:
    def __init__(self, service_account_info: Dict):
        if not service_account_info:
            raise ValueError("Google service account info is required")

        self.creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        self.service = build("drive", "v3", credentials=self.creds)

    def list_files(self, folder_id: str, q: Optional[str] = None) -> List[Dict]:
        if not self.service:
            return []
        
        query = f"'{folder_id}' in parents and trashed = false"
        if q:
            query += f" and ({q})"
        
        results = self.service.files().list(
            q=query,
            fields="files(id, name, createdTime, mimeType)",
            orderBy="createdTime desc"
        ).execute()
        
        return results.get("files", [])

    def download_file(self, file_id: str) -> bytes:
        if not self.service:
            raise ValueError("Google Drive service not initialized")
            
        request = self.service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        return file_io.getvalue()
