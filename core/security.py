"""
Security definitions and safeguards for Project Nikkei.
Enforces Zero-Trust secrets and ensures RCE safeguards via dynamic interactive reviews.
"""

import keyring
import subprocess

import hmac
import hashlib

SERVICE_NAME = "nikkei_os"


def set_secret(key: str, value: str) -> None:
    """Securely store a secret using the system keyring."""
    keyring.set_password(SERVICE_NAME, key, value)


def get_secret(key: str) -> str:
    """Retrieve a secure secret from the system keyring."""
    return keyring.get_password(SERVICE_NAME, key)


def delete_secret(key: str) -> None:
    """Delete a secure secret from the system keyring."""
    keyring.delete_password(SERVICE_NAME, key)


def generate_signature(payload: str) -> str:
    """
    Cryptographic Signatures (HMAC-SHA256).
    Signs a JSON payload using the local DAAQ_SECRET_KEY to prevent
    Poisoned Mailbox attacks in Hostile Territory (cloud sync folders).
    """
    secret = get_secret("DAAQ_SECRET_KEY")
    if not secret:
        raise ValueError("DAAQ_SECRET_KEY not found in keyring. Cannot sign payload.")
        
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def verify_signature(payload: str, signature: str) -> bool:
    """
    Verifies the HMAC-SHA256 signature of an incoming payload.
    """
    try:
        expected_signature = generate_signature(payload)
        return hmac.compare_digest(expected_signature, signature)
    except ValueError:
        return False


def require_interactive_approval(action_description: str) -> bool:
    """
    RCE Safeguard: Any destructive or mutative action MUST trigger 
    an interactive [Approve] / [Reject] button in the Chat Adapter.
    For local or fallback modes, we use an interactive terminal prompt.
    """
    print(f"\n[SECURITY ALERT] Destructive or Mutative Action Requested:")
    print(f"Action: {action_description}")
    # In production, this hooks into the UI/Chat Adapter.
    response = input("Do you approve this action? [Approve/Reject]: ").strip().lower()
    return response in ["approve", "y", "yes"]


def safe_execute(command: list[str]) -> subprocess.CompletedProcess:
    """
    Process Execution safeguard. shell=True is strictly forbidden.
    Always pass lists of arguments to subprocess.run.
    """
    # Enforces shell=False to prevent injection attacks
    return subprocess.run(command, shell=False, capture_output=True, text=True)
