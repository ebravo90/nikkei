"""
File Watchdog for Project Nikkei.
Monitors the tentacles directory in real-time. If a developer edits or creates a Python script
that fails the AST/Hash checks, it triggers a desktop notification.
"""
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core.registry import plugin_registry
from ui.tray_app import show_security_alert


class TentacleSecurityHandler(FileSystemEventHandler):
    """Listens for modifications to tentacles and proactively runs AST security checks."""

    def on_created(self, event):
        self._check_file(event)

    def on_modified(self, event):
        self._check_file(event)

    def _check_file(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # We add a small delay because the file might still be writing to disk
        time.sleep(0.1)

        print(f"[Watchdog] Detected change in {filename}. Scanning...")
        
        # Clear any old quarantine record for this file first
        if filename in plugin_registry.quarantined:
            del plugin_registry.quarantined[filename]
            
        success = plugin_registry.check_file_security(filepath, filename)
        
        if not success and filename in plugin_registry.quarantined:
            reason = plugin_registry.quarantined[filename]
            show_security_alert(filename, reason)


def start_watchdog(tentacles_dir: str = None) -> Observer:
    """Starts the real-time background watchdog."""
    if tentacles_dir is None:
        tentacles_dir = os.path.join(os.path.dirname(__file__), '..', 'tentacles')
        
    event_handler = TentacleSecurityHandler()
    observer = Observer()
    observer.schedule(event_handler, tentacles_dir, recursive=False)
    observer.start()
    
    print(f"[Watchdog] Started monitoring {tentacles_dir} for security violations.")
    return observer
