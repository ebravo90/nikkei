"""
Process Tamer Tentacle for Project Nikkei.
Safely queries and terminates processes using psutil without native root commands.
"""
import psutil
from pydantic import BaseModel, Field
from typing import Dict, Any

from tentacles.base import Tentacle


class ProcessTamerArgs(BaseModel):
    process_name: str = Field(..., description="The name or partial name of the target process")
    action: str = Field(..., description="The action to perform: 'status', or 'kill'")


class ProcessTamerTentacle(Tentacle):
    """
    Searches for processes by name and can retrieve their status or kill them.
    Killing processes implicitly requires interactive approval.
    """
    tool_name = "process_tamer"
    tool_description = "Searches for processes by name and can retrieve their status or terminate them."
    args_schema = ProcessTamerArgs
    requires_approval = True  # Modifying processes requires Zero-Trust verification

    def _execute(self, process_name: str, action: str) -> Dict[str, Any]:
        print(f"[ProcessTamer Tentacle] Target: {process_name} | Action: {action}")
        
        # Override requirement for simple status checks
        if action.lower() == "status":
            self.requires_approval = False
            
        action = action.lower()
        if action not in ["status", "kill"]:
            return {"status": "error", "message": f"Invalid action '{action}'. Must be 'status' or 'kill'."}

        results = []
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    if action == 'kill':
                        proc.terminate()
                        results.append(f"Terminated {proc.info['name']} (PID: {proc.info['pid']})")
                    else:
                        results.append(f"Found {proc.info['name']} (PID: {proc.info['pid']}) - Status: {proc.info['status']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if not results:
            return {"status": "not_found", "message": f"No process found matching '{process_name}'"}
            
        return {"status": "success", "results": results}
