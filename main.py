"""
Main Entry Point for Project Nikkei.
Initializes the Plugin Registry, the AgentZero router, and attempts to boot
the Telegram Adapter. Gracefully falls back to a local CLI loop if keys are missing.
"""
import sys
from pprint import pprint

from core.registry import plugin_registry
from core.agent_zero import AgentZero
from core.security import get_secret
from core.watcher import start_watchdog
from adapters.chat.telegram import TelegramAdapter
from ui.oauth_server import start_server
from ui.tray_app import start_tray_app
from core.insomnia import insomnia_manager


def initialize_system():
    """Bootstraps the registry and components."""
    print("[Nikkei OS] Initializing core components...")
    
    # 1. Load available tools into the registry
    plugin_registry.load_tentacles()
    plugin_registry.load_neurons()
    
    loaded_tools = plugin_registry.get_all_tool_schemas()
    print(f"[Nikkei OS] Registry initialized. Loaded {len(loaded_tools)} tools.")
    
    # 2. Instantiate the Router
    agent_zero = AgentZero()
    return agent_zero


def start_cli_fallback(agent: AgentZero):
    """
    Local fallback CLI loop for interactive testing without setting up Chat Webhooks.
    """
    print("\n" + "="*50)
    print("Project Nikkei Local CLI Fallback Mode")
    print("Zero-Trust Architecture: ENABLED")
    print("Type 'exit' or 'quit' to terminate.")
    print("="*50 + "\n")
    
    while True:
        try:
            prompt = input("\nNikkei-User> ")
            if not prompt.strip():
                continue
            if prompt.lower() in ['exit', 'quit']:
                print("Shutting down Project Nikkei...")
                break
                
            # Send the natural language command to Agent Zero
            result = agent.process_prompt(prompt)
            
            print("\n[Execution Result]:")
            pprint(result, indent=2)
            
        except KeyboardInterrupt:
            print("\nShutting down Project Nikkei...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[FATAL ERROR]: {e}")


def main():
    """Main execution loop."""
    try:
        agent = initialize_system()
        
        # Start Background Services
        print("\n[Nikkei OS] Starting background services...")
        insomnia_manager.keep_awake()
        start_watchdog()
        start_server(port=5000)
        start_tray_app()
        print("[Nikkei OS] Background services online.\n")
        
        # 3. Attempt to initialize the Chat Adapter
        # Check if we have the necessary credentials
        bot_token = get_secret("TELEGRAM_BOT_TOKEN")
        
        if bot_token:
            print("[Nikkei OS] Telegram credentials found. Booting Chat Adapter...")
            try:
                admin_id = get_secret("TELEGRAM_ADMIN_CHAT_ID")
                if admin_id:
                    import socket
                    import platform
                    import requests
                    from datetime import datetime
                    
                    try:
                        msg = (f"🟢 <b>Nikkei Node Online</b>\n"
                               f"🖥️ <b>Host:</b> {socket.gethostname()}\n"
                               f"📍 <b>OS:</b> {platform.system()}\n"
                               f"🕒 <b>Boot Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                               f"📡 <b>Status:</b> Awaiting directives.")
                        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        requests.post(url, json={"chat_id": admin_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
                    except Exception as e:
                        print(f"[Nikkei OS] Failed to send boot notification: {e}")

                telegram_adapter = TelegramAdapter()
                # Under normal ptb this would block and listen indefinitely
                telegram_adapter.start_listening()
                print("[Nikkei OS] Telegram Adapter started successfully.")
            except Exception as e:
                print(f"[Nikkei OS] Failed to start Telegram Adapter: {e}. Falling back to CLI.")
                start_cli_fallback(agent)
        else:
            print("[Nikkei OS] Missing TELEGRAM_BOT_TOKEN in keyring.")
            print("[Nikkei OS] Falling back to interactive CLI mode.")
            start_cli_fallback(agent)
    except KeyboardInterrupt:
        pass
    finally:
        insomnia_manager.allow_sleep()
        print("[Nikkei OS] System shutdown complete.")


if __name__ == "__main__":
    main()
