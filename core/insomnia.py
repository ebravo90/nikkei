"""
Cross-platform Anti-Sleep Manager for Project Nikkei.
Prevents the host OS from going to sleep or hibernating while the OS is running.
"""
import os
import platform
import logging
import subprocess

class Insomnia:
    def __init__(self):
        self.os_type = platform.system()
        self.caffeinate_process = None
        self.inhibit_process = None

    def keep_awake(self):
        """Attempts to prevent the system from sleeping using OS-specific methods."""
        logging.info(f"[Insomnia] Initializing anti-sleep protocols for {self.os_type}...")
        
        try:
            if self.os_type == 'Windows':
                import ctypes
                # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
                ES_CONTINUOUS = 0x80000000
                ES_SYSTEM_REQUIRED = 0x00000001
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
                logging.info("[Insomnia] Windows ThreadExecutionState set to prevent sleep.")
                
            elif self.os_type == 'Darwin':  # macOS
                # 'caffeinate -i' prevents idle sleep. '-w <pid>' waits for Nikkei to exit.
                pid = str(os.getpid())
                self.caffeinate_process = subprocess.Popen(
                    ['caffeinate', '-i', '-w', pid], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                logging.info(f"[Insomnia] macOS caffeinate launched for PID {pid}.")
                
            elif self.os_type == 'Linux':
                # Attempt to use systemd-inhibit
                self.inhibit_process = subprocess.Popen(
                    ['systemd-inhibit', '--what=sleep:idle', '--why=Nikkei OS Background Services', 'sleep', 'infinity'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logging.info("[Insomnia] Linux systemd-inhibit launched.")
            else:
                logging.warning(f"[Insomnia] Unsupported OS: {self.os_type}. Anti-sleep not applied.")
                
        except Exception as e:
            logging.warning(f"[Insomnia] Failed to apply anti-sleep protocol: {e}")

    def allow_sleep(self):
        """Restores normal sleep behavior gracefully."""
        logging.info("[Insomnia] Reverting anti-sleep protocols. Allowing system sleep...")
        
        try:
            if self.os_type == 'Windows':
                import ctypes
                ES_CONTINUOUS = 0x80000000
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                logging.info("[Insomnia] Windows ThreadExecutionState reverted.")
                
            elif self.os_type == 'Darwin':
                if self.caffeinate_process:
                    self.caffeinate_process.terminate()
                    self.caffeinate_process.wait(timeout=2)
                    logging.info("[Insomnia] macOS caffeinate terminated.")
                    
            elif self.os_type == 'Linux':
                if self.inhibit_process:
                    self.inhibit_process.terminate()
                    self.inhibit_process.wait(timeout=2)
                    logging.info("[Insomnia] Linux systemd-inhibit terminated.")
                    
        except Exception as e:
            logging.warning(f"[Insomnia] Error while reverting anti-sleep: {e}")

# Global singleton instance for easy access
insomnia_manager = Insomnia()
