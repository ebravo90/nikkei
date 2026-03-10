"""
Base Tentacle blueprint for Project Nikkei.
Tentacles are atomic, single-shot actions (e.g., executing a system command, Jira API).
"""
from abc import ABC, abstractmethod
from typing import Any, Type, Optional
from pydantic import BaseModel

from core.security import require_interactive_approval


class Sucker(ABC):
    """
    Data extractor component (Suction Cup) for a Tentacle.
    Uses AI grounding to fetch and format real-world/live data.
    """
    @abstractmethod
    def extract(self, query: str) -> Any:
        """Extracts data based on the provided query prompt."""
        pass


class Tentacle(ABC):
    """
    Base class for all Tentacles.
    
    Attributes:
        tool_name (str): The unique identifier for the tool.
        tool_description (str): Description of what the tool does, for LLM routing.
        args_schema (Type[BaseModel]): Pydantic schema for arguments validation.
        requires_approval (bool): If True, triggers RCE safeguards before execution.
        is_tentacle (bool): Marker for the dynamic registry loader.
    """
    is_tentacle: bool = True
    tool_name: str
    tool_description: str
    args_schema: Optional[Type[BaseModel]] = None
    requires_approval: bool = False

    def __init__(self, sucker: Optional[Sucker] = None):
        """
        Initialization logic for setting up connections if needed.
        Can optionally accept a Sucker component for data extraction.
        """
        self.sucker = sucker
        # Validate that subclasses implement necessary attributes
        if not hasattr(self, "tool_name"):
            raise NotImplementedError("Tentacle must define a 'tool_name'")
        if not hasattr(self, "tool_description"):
            raise NotImplementedError("Tentacle must define a 'tool_description'")

    def execute(self, **kwargs) -> Any:
        """
        Wrapper around the abstract implementation to enforce security hooks.
        """
        bypass_token = kwargs.pop("bypass_token", None)
        
        if self.requires_approval:
            # RCE Safeguards triggered
            approved = require_interactive_approval(
                f"Executing Tentacle: {self.tool_name} with args {kwargs}",
                bypass_token=bypass_token
            )
            if not approved:
                return {
                    "status": "rejected",
                    "message": f"Execution of {self.tool_name} was rejected by the admin."
                }
                
        return self._execute(**kwargs)

    @abstractmethod
    def _execute(self, **kwargs) -> Any:
        """
        The actual implementation of the tool's logic.
        """
        pass
