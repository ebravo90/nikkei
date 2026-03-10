"""
Base Chat Interface for Project Nikkei.
Defines required methods for all chat communication channels.
"""
from abc import ABC, abstractmethod


class ChatInterface(ABC):
    """
    Abstract base class for establishing chat communication.
    Must implement listeners, message senders, and the interactive RCE approval mechanism.
    """
    @abstractmethod
    def start_listening(self) -> None:
        """
        Starts polling or opens webhooks/sockets to receive inbound messages.
        """
        pass

    @abstractmethod
    def send_message(self, text: str) -> None:
        """
        Pushes a text message back to the user via the chat interface.
        """
        pass

    @abstractmethod
    def ask_for_approval(self, action_description: str) -> bool:
        """
        Sends an interactive UI (e.g., [Approve] / [Reject] buttons) to the chat.
        Blocks or yields until the administrator makes a decisive choice.
        
        Args:
            action_description (str): Description of the RCE or mutative action.
            
        Returns:
            bool: True if approved, False if rejected or timeout.
        """
        pass
