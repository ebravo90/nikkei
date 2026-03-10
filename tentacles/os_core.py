import os
import platform
from pydantic import Field

from tentacles.base import Tentacle


class OSCoreTentacle(Tentacle):
    """
    Provides native Operating System and filesystem tools without relying on `subprocess`.
    Essential for circumventing `shell=False` restrictions on builtins like `dir` or `pwd`.
    Use this tentacle sequentially to explore directories before reading files.
    """
    
    name = "os_core"
    description = "A suite of native Python OS functions for system navigation and host inspection."
    version = "1.0.0"

    parameters = {
        "action": Field(
            description="The specific OS action to execute.",
            enum=["get_cwd", "list_dir", "system_info"]
        ),
        "target_path": Field(
            default=".",
            description="The target directory path when listing directories. Defaults to current directory."
        )
    }

    def execute(self, action: str, target_path: str = ".", **kwargs) -> str:
        """Executes the specified native OS operation."""
        try:
            if action == "get_cwd":
                return f"Current Working Directory: {os.getcwd()}"
                
            elif action == "list_dir":
                # Ensure the path exists
                if not os.path.exists(target_path):
                    return f"Error: Path '{target_path}' does not exist."
                if not os.path.isdir(target_path):
                    return f"Error: Path '{target_path}' is not a directory."
                    
                items = os.listdir(target_path)
                
                # Enhance the output by identifying files vs directories
                formatted_items = []
                for item in items:
                    full_path = os.path.join(target_path, item)
                    if os.path.isdir(full_path):
                        formatted_items.append(f"[DIR]  {item}")
                    else:
                        formatted_items.append(f"[FILE] {item}")
                        
                result = f"Directory contents of '{target_path}':\n"
                result += "\n".join(sorted(formatted_items))
                return result
                
            elif action == "system_info":
                uname = platform.uname()
                # Use standard standard library attributes smoothly
                return (f"System Info:\n"
                        f"System: {uname.system}\n"
                        f"Node Name: {uname.node}\n"
                        f"Release: {uname.release}\n"
                        f"Version: {uname.version}\n"
                        f"Machine: {uname.machine}\n"
                        f"Processor: {uname.processor}")
                        
            else:
                return f"Error: Unsupported action '{action}'."
                
        except PermissionError:
            return f"Error: Permission denied attempting OS action: '{action}' on '{target_path}'."
        except Exception as e:
            return f"Error executing OS Core operation '{action}': {str(e)}"
