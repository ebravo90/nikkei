"""
Base Neuron blueprint for Project Nikkei.
Neurons are complex orchestrators and state machines (e.g., SDLC workflows).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel


class Neuron(ABC):
    """
    Base class for all Neurons.
    
    Attributes:
        tool_name (str): The unique identifier for the orchestrator.
        tool_description (str): Description of the workflow for LLM routing.
        args_schema (Type[BaseModel]): Pydantic schema for arguments validation.
        max_iterations (int): Circuit breaker to prevent infinite agent loops.
        is_neuron (bool): Marker for the dynamic registry loader.
    """
    is_neuron: bool = True
    tool_name: str
    tool_description: str
    args_schema: Optional[Type[BaseModel]] = None
    max_iterations: int = 3

    def __init__(self):
        # Validate subclass definitions
        if not hasattr(self, "tool_name"):
            raise NotImplementedError("Neuron must define a 'tool_name'")
        if not hasattr(self, "tool_description"):
            raise NotImplementedError("Neuron must define a 'tool_description'")

    def execute(self, state: Dict[str, Any] = None, **kwargs) -> Any:
        """
        Wrapper to enforce circuit breakers and state management.
        """
        if state is None:
            # Initialize state with incoming arguments
            state = {"iterations": 0, "status": "initialized", "data": kwargs}
            
        return self._execute(state)

    @abstractmethod
    def _execute(self, state: Dict[str, Any]) -> Any:
        """
        The actual state machine workflow implementation.
        Must respect self.max_iterations to prevent infinite loops.
        """
        pass
