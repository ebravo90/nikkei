"""
Google Drive (Real Output) Queue explicitly implementing CloudQueueAdapter.
Uses google-api-python-client to upload/download cryptographically signed DaaQ JSON payloads.
"""
import os
import json
import uuid
import logging
from typing import Dict, List, Any

# Google API Clients
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from adapters.queue.base import CloudQueueAdapter

# Require Drive File scope to restrict to files created by the app
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GDriveQueueAdapter(CloudQueueAdapter):
    """
    Fully functional Drive-as-a-Queue integration utilizing Google Workspace REST API.
    Uploads signed payloads to an isolated cloud folder to prevent Poisoned Mailbox vectors.
    """
    def __init__(self, folder_id: str = None):
        self.folder_id = folder_id
        self.creds = None
        self._authenticate()
        
        if self.creds:
            self.service = build('drive', 'v3', credentials=self.creds)
        else:
            self.service = None
            logging.error("[GDrive Queue] Authentication failed. Adapter inactive.")

    def _authenticate(self):
        """Authenticates the user and fetches the credentials.json or token.json."""
        token_path = os.path.expanduser('~/.nikkei_token.json')
        creds_path = os.path.expanduser('~/.nikkei_credentials.json')

        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logging.error(f"[GDrive Queue] Error refreshing Google token: {e}")
                    self.creds = None
            elif os.path.exists(creds_path):
                # We need credentials.json provided by Google Cloud Console
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                # In headless, this will print a URL for the user to visit
                self.creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            if self.creds:
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())

    def _save_task_file(self, target_machine_id: str, signed_package: Dict[str, str]) -> bool:
        """
        Uploads the signed .json package definitively to the Drive endpoint.
        Format: targetMachineId_uuid.json
        """
        if not self.service:
            return False
            
        task_id = f"{target_machine_id}_{uuid.uuid4().hex}"
        file_name = f"{task_id}.json"
        
        file_metadata = {'name': file_name}
        if self.folder_id:
            file_metadata['parents'] = [self.folder_id]
            
        payload_bytes = json.dumps(signed_package).encode('utf-8')

        try:
            import io
            media = MediaIoBaseUpload(io.BytesIO(payload_bytes), mimetype='application/json', resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"[GDrive Queue (Real)] Enqueued task: {file_name} (File ID: {file.get('id')})")
            return True
        except Exception as e:
            logging.error(f"[GDrive Queue (Real)] Failed to persist to cloud: {e}")
            return False

    def _read_task_files(self, my_machine_id: str) -> List[tuple[str, Dict[str, Any]]]:
        """
        Queries the Drive API for .json files explicitly allocated to `my_machine_id`.
        """
        if not self.service:
            return []
            
        tasks = []
        query = f"name contains '{my_machine_id}_' and name contains '.json' and trashed=false"
        if self.folder_id:
            query += f" and '{self.folder_id}' in parents"
            
        try:
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])

            for item in items:
                file_id = item['id']
                file_name = item['name']
                try:
                    content = self.service.files().get_media(fileId=file_id).execute()
                    package = json.loads(content)
                    # We store the Drive file ID as task_id to delete it later
                    tasks.append((file_id, package))
                except Exception as e:
                    logging.warning(f"Could not read/parse Drive file {file_name}: {e}. Skipping.")
        except Exception as e:
            logging.error(f"[GDrive Queue (Real)] API List IOError: {e}")
            
        return tasks

    def delete_task(self, task_id: str) -> None:
        """
        Deletes the executed payload definitively from the cloud index.
        task_id here actually specifies the remote Google Drive File ID.
        """
        if not self.service:
            return
            
        try:
            self.service.files().delete(fileId=task_id).execute()
            print(f"[GDrive Queue (Real)] Cloud entity deleted: {task_id}")
        except Exception as e:
            logging.error(f"[GDrive Queue (Real)] Failed to delete remote file {task_id}: {e}")
