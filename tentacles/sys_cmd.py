"""
System Command Tentacle for Project Nikkei.
Executes arbitrary local OS commands enforcing shell=False validation.
"""
import shlex
from pydantic import BaseModel, Field
from typing import Dict, Any

from tentacles.base import Tentacle
from core.security import safe_execute


class SysCmdArgs(BaseModel):
    command: str = Field(..., description="The shell command to execute (e.g., 'ls -la', 'pwd', 'ping 8.8.8.8')")


class SysCmdTentacle(Tentacle):
    """
    Executes an OS command natively and securely.
    """
    tool_name = "sys_cmd"
    tool_description = "Executes arbitrary system commands on the local machine."
    args_schema = SysCmdArgs
    requires_approval = True  # Strict Zero-Trust requirement for any bash/cmd operation

    def _execute(self, command: str) -> Dict[str, Any]:
        print(f"[SysCmd Tentacle] Parsing command: {command}")
        try:
            parsed_cmd = shlex.split(command)
            result = safe_execute(parsed_cmd)
        except Exception as e:
            return {
                "status": "fatal_error",
                "error": str(e)
            }
            
        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout.strip() if result.stdout else "",
            "stderr": result.stderr.strip() if result.stderr else "",
            "returncode": result.returncode
        }
