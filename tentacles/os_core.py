import os
import platform
from pydantic import BaseModel, Field
from typing import Dict, Any

from tentacles.base import Tentacle


class OSCoreArgs(BaseModel):
    action: str = Field(..., description="The specific OS action to execute.", json_schema_extra={"enum": ["get_cwd", "list_dir", "system_info"]})
    target_path: str = Field(default=".", description="The target directory path when listing directories. Defaults to current directory.")


class OSCoreTentacle(Tentacle):
    """
    Provides native Operating System and filesystem tools without relying on `subprocess`.
    Essential for circumventing `shell=False` restrictions on builtins like `dir` or `pwd`.
    Use this tentacle sequentially to explore directories before reading files.
    """
    
    tool_name = "os_core"
    tool_description = "A suite of native Python OS functions for system navigation and host inspection."
    args_schema = OSCoreArgs
    requires_approval = False

    def _execute(self, action: str, target_path: str = ".", **kwargs) -> Dict[str, Any]:
        """Executes the specified native OS operation."""
        try:
            if action == "get_cwd":
                return {
                    "status": "success",
                    "result": f"Current Working Directory: {os.getcwd()}"
                }
                
            elif action == "list_dir":
                if not os.path.exists(target_path):
                    return {"status": "error", "error": f"Path '{target_path}' does not exist."}
                if not os.path.isdir(target_path):
                    return {"status": "error", "error": f"Path '{target_path}' is not a directory."}
                    
                items = os.listdir(target_path)
                
                formatted_items = []
                for item in items:
                    full_path = os.path.join(target_path, item)
                    if os.path.isdir(full_path):
                        formatted_items.append(f"[DIR]  {item}")
                    else:
                        formatted_items.append(f"[FILE] {item}")
                        
                result = f"Directory contents of '{target_path}':\n"
                result += "\n".join(sorted(formatted_items))
                return {
                    "status": "success",
                    "result": result
                }
                
            elif action == "system_info":
                uname = platform.uname()
                info = (f"System Info:\n"
                        f"System: {uname.system}\n"
                        f"Node Name: {uname.node}\n"
                        f"Release: {uname.release}\n"
                        f"Version: {uname.version}\n"
                        f"Machine: {uname.machine}\n"
                        f"Processor: {uname.processor}")
                return {
                    "status": "success",
                    "result": info
                }
                        
            else:
                return {"status": "error", "error": f"Unsupported action '{action}'."}
                
        except PermissionError:
            return {"status": "error", "error": f"Permission denied attempting OS action: '{action}' on '{target_path}'."}
        except Exception as e:
            return {"status": "error", "error": f"Error executing OS Core operation '{action}': {str(e)}"}
