"""
Developer Testing Harness for Project Nikkei (SDET Sandbox).
Provides a CLI to test specific Target functions (Tentacles/Neurons) directly, 
bypassing AgentZero and LLM inference for cost-free validation.
"""
import argparse
import json
import sys
import os
import time
import hashlib
from pprint import pprint
from pydantic import ValidationError

from core.registry import plugin_registry
from core.security import get_secret, set_secret


def main():
    parser = argparse.ArgumentParser(description="Project Nikkei Developer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # "test" subcommand
    test_parser = subparsers.add_parser("test", help="Test a specific LLM tool (Tentacle or Neuron)")
    test_parser.add_argument("tool_name", type=str, help="The exact tool_name of the plugin to test")
    test_parser.add_argument(
        "--mock-args", 
        type=str, 
        default="{}", 
        help="JSON string representing the arguments to pass to the tool"
    )

    # "status" subcommand
    subparsers.add_parser("status", help="Print system vital signs (Telemetry)")

    # "quarantine" subcommand
    quarantine_parser = subparsers.add_parser("quarantine", help="Manage quarantined files (Headless Dashboard)")
    quarantine_subparsers = quarantine_parser.add_subparsers(dest="q_command", help="Quarantine actions")
    
    quarantine_subparsers.add_parser("list", help="List quarantined and currently whitelisted files")
    
    q_approve_parser = quarantine_subparsers.add_parser("approve", help="Approve and whitelist a quarantined file")
    q_approve_parser.add_argument("filename", type=str, help="The exact filename (e.g. 'my_tentacle.py') to approve")

    args = parser.parse_args()

    if args.command == "test":
        _run_test_sandbox(args.tool_name, args.mock_args)
    elif args.command == "status":
        _run_status_telemetry()
    elif args.command == "quarantine":
        _run_quarantine_cmd(args)
    else:
        parser.print_help()


def _run_status_telemetry():
    """Prints the telemetry vital signs for the system."""
    # Note: In a real system, you'd probably check actual running processes,
    # but for this CLI, we check configurations and mock the active state.
    from core.security import get_secret
    
    print("\n[Nikkei OS Telemetry]")
    print("="*40)
    
    # Check AgentZero
    # For Status CLI, we assume offline if we can't initialize it,
    # but here we'll just report it as "Online (Configured)"
    print("🟢 Agent: Online (Configured)")
    
    # Check Chat Adapter
    bot_token = get_secret("TELEGRAM_BOT_TOKEN")
    if bot_token:
        print("💬 Chat: Telegram (Configured)")
    else:
        print("💬 Chat: Disconnected")
        
    # Check DaaQ Status
    import os
    from pathlib import Path
    try:
        sync_dir = Path(os.path.expanduser("~/.nikkei_queue_mock"))
        if sync_dir.exists():
            pending = list(sync_dir.glob("*.json"))
            print(f"☁️  DaaQ: GDrive Mock - {len(pending)} Pending Tasks")
        else:
            print("☁️  DaaQ: GDrive Mock - Not initialized")
    except Exception:
        print("☁️  DaaQ: GDrive Mock - Error")
        
    print("🤖 Active Nodes/Instances: 1 Local Node")
    print("="*40 + "\n")


def _run_quarantine_cmd(args):
    """Execution Logic for the headless quarantine management."""
    plugin_registry.load_tentacles()
    
    if args.q_command == "list":
        print("\n[🛡️  Nikkei Security Quarantine]")
        print("="*40)
        
        # Display Quarantine
        print("\n--- Currently Quarantined ---")
        if not plugin_registry.quarantined:
            print("  No items currently in quarantine.")
        else:
            for fname, reason in plugin_registry.quarantined.items():
                print(f"  [BLOCKED] {fname} -> Reason: {reason}")
                
        # Display Whitelist
        print("\n--- Currently Whitelisted ---")
        whitelist_str = get_secret("WHITELISTED_TENTACLES") or "{}"
        try:
            whitelist = json.loads(whitelist_str)
        except json.JSONDecodeError:
            whitelist = {}
            
        if not whitelist:
            print("  No items currently whitelisted.")
        else:
            for fname, hsh in whitelist.items():
                print(f"  [SAFE] {fname} -> SHA256:{hsh[:8]}...")
                
        print("\n" + "="*40 + "\n")
        
    elif args.q_command == "approve":
        filename = args.filename
        filepath = os.path.join(os.path.dirname(__file__), 'tentacles', filename)
        
        if not os.path.exists(filepath):
            print(f"[Error] File '{filename}' not found in tentacles/ directory.")
            sys.exit(1)
            
        print("\n[🚨 SECURITY WARNING 🚨]")
        print("You are granting this script RAW OS EXECUTION RIGHTS.")
        print(f"Target: {filename}")
        print("="*40)
        
        # The Xiaomi Delay
        for i in range(5, 0, -1):
            sys.stdout.write(f"\rApproving in {i}... ")
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\rApproving in 0... \n")
            
        # The Hasher
        print("\n[1] Computing strict SHA-256 hash...")
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        computed_hash = hasher.hexdigest()
        print(f"    -> Hash: {computed_hash}")
        
        # The Save
        print("[2] Updating secure Keyring whitelist...")
        whitelist_str = get_secret("WHITELISTED_TENTACLES") or "{}"
        try:
            whitelist = json.loads(whitelist_str)
        except json.JSONDecodeError:
            whitelist = {}
            
        whitelist[filename] = computed_hash
        set_secret("WHITELISTED_TENTACLES", json.dumps(whitelist))
        
        print(f"\n[✅ SUCCESS] '{filename}' is now strictly whitelisted for execution.")
        
    else:
        print("[Error] Invalid quarantine command. Use 'list' or 'approve'.")


def _run_test_sandbox(tool_name: str, mock_args_str: str):
    """Execution Logic for the developer sandbox testing a specific tool."""
    print("\n[Nikkei SDET Sandbox]")
    print(f"Targeting Tool: {tool_name}")
    print(f"Mock Args: {mock_args_str}\n")
    
    # 1. Initialize Registry
    plugin_registry.load_tentacles()
    plugin_registry.load_neurons()
    
    # 2. Find the requested tool
    tool = plugin_registry.get_tentacle(tool_name) or plugin_registry.get_neuron(tool_name)
    if not tool:
        print(f"[Error] Tool '{tool_name}' not found in the initialized registry.")
        sys.exit(1)
        
    print(f"[Found Tool] -> {tool.__class__.__name__}")
    
    # 3. Parse JSON arguments
    try:
        kwargs = json.loads(mock_args_str)
    except json.JSONDecodeError as e:
        print(f"[Error] Failed to parse --mock-args JSON: {e}")
        sys.exit(1)
        
    # 4. Validate parsed JSON against the tool's Pydantic schema
    if hasattr(tool, "args_schema") and tool.args_schema:
        print("[Validating Schema]")
        try:
            validated_args = tool.args_schema(**kwargs)
            kwargs = validated_args.model_dump()
            print(" -> Valid Match ✓")
        except ValidationError as ve:
            print("[Error] Pydantic Validation Error (Simulated LLM Hallucination):")
            for error in ve.errors():
                print(f"  - {error['loc']}: {error['msg']}")
            sys.exit(1)
    else:
        print("[Notice] Tool has no args_schema. Sending unchecked kwargs.")

    # 5. Execute functionality
    print("\n[Executing Logic] ->")
    try:
        if hasattr(tool, "execute"):
            result = tool.execute(**kwargs)
        else:
            result = tool(**kwargs)
            
        print("\n[Result]:")
        pprint(result, indent=2)
    except Exception as e:
        print(f"\n[Execution Exception]: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
