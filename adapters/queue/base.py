"""
Base Queue Interface (DaaQ) for Project Nikkei.
Defines required methods for offline P2P queue adapters syncing via third-party storage. 
Must strictly implement Cryptographic Signatures to prevent Poisoned Mailbox attacks.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from core.security import generate_signature, verify_signature


class CloudQueueAdapter(ABC):
    """
    Abstract base class for Drive-as-a-Queue (DaaQ) adapters.
    """
    def enqueue_task(self, target_machine_id: str, task_payload: Dict[str, Any]) -> bool:
        """
        Serializes and cryptographically signs a payload to prevent tampering.
        Saves the resulting package to the "Hostile Territory" cloud queue.
        """
        payload_str = json.dumps(task_payload, sort_keys=True)
        try:
            signature = generate_signature(payload_str)
        except ValueError as e:
            logging.error(f"Failed to sign payload: {e}")
            return False
            
        signed_package = {
            "payload": payload_str,
            "signature": signature
        }
        
        return self._save_task_file(target_machine_id, signed_package)

    def fetch_pending_tasks(self, my_machine_id: str) -> List[Dict[str, Any]]:
        """
        Reads pending task files targeted at this machine.
        MUST verify cryptographic signatures. Invalid files are discarded and deleted.
        """
        valid_tasks = []
        raw_files = self._read_task_files(my_machine_id)
        
        for task_id, package in raw_files:
            payload_str = package.get("payload", "")
            signature = package.get("signature", "")
            
            if not payload_str or not signature:
                logging.warning(f"Malformed task {task_id}. Deleting...")
                self.delete_task(task_id)
                continue
                
            if verify_signature(payload_str, signature):
                try:
                    payload_dict = json.loads(payload_str)
                    payload_dict["_task_id"] = task_id  # Inject ID for later deletion
                    valid_tasks.append(payload_dict)
                except json.JSONDecodeError:
                    logging.warning(f"Unparsable valid JSON in task {task_id}. Deleting...")
                    self.delete_task(task_id)
            else:
                logging.error(f"[SECURITY ALERT] Invalid signature for task {task_id}. Possible Poisoned Mailbox attack. Deleting.")
                self.delete_task(task_id)
                
        return valid_tasks

    @abstractmethod
    def _save_task_file(self, target_machine_id: str, signed_package: Dict[str, str]) -> bool:
        """
        Internal implementation to physically save the file (cloud/local).
        """
        pass

    @abstractmethod
    def _read_task_files(self, my_machine_id: str) -> List[tuple[str, Dict[str, Any]]]:
        """
        Internal implementation to read all pending tasks for a machine ID.
        Returns a list of tuples (task_id, signed_package).
        """
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> None:
        """
        Removes the file once successfully executed or deemed malicious.
        """
        pass
