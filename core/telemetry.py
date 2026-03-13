import time
import socket
import platform
import json
import threading
from datetime import datetime, timezone
from adapters.queue.gdrive import GDriveQueueAdapter

def start_telemetry_heartbeat():
    """Starts a background thread that sends a DaaQ heartbeat every 3 minutes."""
    def _heartbeat_worker():
        node_id = socket.gethostname()
        os_name = platform.system()
        file_name = f"{node_id}_heartbeat.json"
        
        while True:
            try:
                gdrive = GDriveQueueAdapter()
                if gdrive.service:
                    payload = {
                        "node_id": node_id,
                        "os": os_name,
                        "status": "online",
                        "last_seen_utc": datetime.now(timezone.utc).isoformat()
                    }
                    
                    query = f"name = '{file_name}' and trashed=false"
                    results = gdrive.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
                    items = results.get('files', [])
                    
                    import io
                    from googleapiclient.http import MediaIoBaseUpload
                    payload_bytes = json.dumps(payload).encode('utf-8')
                    media = MediaIoBaseUpload(io.BytesIO(payload_bytes), mimetype='application/json', resumable=True)
                    
                    if items:
                        # Overwrite existing
                        file_id = items[0]['id']
                        gdrive.service.files().update(fileId=file_id, media_body=media).execute()
                    else:
                        # Create new
                        file_metadata = {'name': file_name}
                        gdrive.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            except Exception as e:
                print(f"[Telemetry] Heartbeat failed: {e}")
            
            time.sleep(180)  # 3 minutes
            
    threading.Thread(target=_heartbeat_worker, daemon=True).start()
