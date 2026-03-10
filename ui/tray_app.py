"""
System Tray Vital Signs Monitor for Project Nikkei.
Uses pystray to provide a desktop icon with a clean telemetry menu.
"""
import webbrowser
import threading
import subprocess
import os
import sys
import pystray
from PIL import Image, ImageDraw

def create_image(width, height, color1, color2):
    """Generate a simple tray icon image."""
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    dc.rectangle((0, height // 2, width // 2, height), fill=color2)
    return image

global_icon = None

def show_security_alert(filename: str, reason: str):
    """Desktop notification for quarantined edits."""
    if global_icon:
        global_icon.notify(
            f"Blocked execution of {filename}\nReason: {reason}",
            title="Nikkei Security Guard"
        )
    else:
        print(f"[Tray Null] Could not trigger notification for {filename}")

def open_settings(icon, item):
    """Open the Flask Configuration Portal in the default web browser, trying App mode first."""
    url = 'http://localhost:5000/'
    try:
        if os.name == 'nt': # Windows
            subprocess.Popen(['start', 'msedge', f'--app={url}'], shell=True)
        elif sys.platform == 'darwin': # macOS
            subprocess.Popen(['open', '-na', 'Google Chrome', '--args', f'--app={url}'])
        else:
            webbrowser.open(url)
    except Exception:
        webbrowser.open(url)

def quit_app(icon, item):
    """Cleanly shut down the tray app."""
    # In a full integration, you might want to also signal the Flask server 
    # and main loops to shut down gracefully.
    icon.stop()

def get_menu():
    """Build the clean Vital Signs telemetry menu."""
    return pystray.Menu(
        pystray.MenuItem("🟢 Agent: Online", None, enabled=False),
        pystray.MenuItem("☁️ DaaQ: Synced", None, enabled=False),
        pystray.MenuItem("💬 Chat: Telegram Active", None, enabled=False),
        pystray.MenuItem("------------------------", None, enabled=False),
        pystray.MenuItem("⚙️ Settings & Connections", open_settings),
        pystray.MenuItem("🛑 Quit", quit_app)
    )

def start_tray_app():
    """Launch the pystray icon (must run in the main thread on some platforms, or a dedicated thread)."""
    global global_icon
    # Create a 64x64 simple placeholder icon
    icon_image = create_image(64, 64, 'black', 'white')
    icon = pystray.Icon("NikkeiOS", icon_image, "Nikkei OS", get_menu())
    global_icon = icon
    
    # We run the icon in a thread if it doesn't block, 
    # though on macOS pystray.Icon.run() usually must be in the main thread.
    # For now, we will just provide the invocation method.
    def _run():
        icon.run()
        
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    start_tray_app().join()
