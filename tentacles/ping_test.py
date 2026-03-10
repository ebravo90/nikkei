"""
Ping Test Tentacle for Project Nikkei.
A simple test tool to verify LLM routing and system vitality.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from tentacles.base import Tentacle


class PingTestArgs(BaseModel):
    """Arguments schema for the Ping Test Tentacle."""
    message: Optional[str] = Field(
        default="Ping!", 
        description="An optional message to echo back."
    )


class PingTestTentacle(Tentacle):
    """
    Replies with a simple pong message and the current system time 
    to verify the agent is alive and routing correctly.
    """
    tool_name = "ping_test"
    tool_description = "Replies with a simple pong message and the current system time to verify the agent is alive."
    args_schema = PingTestArgs
    requires_approval = False

    def _execute(self, message: str = "Ping!") -> dict:
        """
        Executes the ping test.
        """
        current_time = datetime.now().isoformat()
        response_text = f"Pong! Received: '{message}'. System local time: {current_time}"
        
        return {
            "status": "success",
            "response": response_text,
            "timestamp": current_time
        }
