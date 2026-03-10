"""
Dynamic Registry Loader for Project Nikkei.
Implements an in-memory Registry Pattern that dynamically loads tools (Tentacles) 
and orchestrators (Neurons) and extracts Pydantic-based JSON schemas for Agent Zero.
"""

import importlib
import pkgutil
import inspect
import ast
import hashlib
import json
import os
from typing import Dict, Any, Callable, Type
from pydantic import BaseModel

from core.security import get_secret


class Registry:
    def __init__(self):
        self.tentacles: Dict[str, Callable] = {}
        self.neurons: Dict[str, Any] = {}
        self.quarantined: Dict[str, str] = {}

    def _compute_hash(self, filepath: str) -> str:
        """Computes the SHA-256 hash of a file's contents."""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def load_tentacles(self, package_name: str = "tentacles") -> None:
        """Dynamically discover and load single-shot Python scripts (Tentacles)."""
        self._load_module(package_name, self.tentacles, expected_type="tentacle")

    def load_neurons(self, package_name: str = "neurons") -> None:
        """Dynamically discover and load complex orchestrators (Neurons)."""
        self._load_module(package_name, self.neurons, expected_type="neuron")

    def check_file_security(self, filepath: str, filename: str) -> bool:
        """Runs AST scan to block unauthorized blacklisted imports and verifies hashes."""
        if not os.path.exists(filepath):
            return False
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            blacklisted_imports = {'os', 'subprocess', 'sys', 'shutil', 'pty'}
            found_blacklist = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] in blacklisted_imports:
                            found_blacklist = True
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in blacklisted_imports:
                        found_blacklist = True
                        
            if found_blacklist:
                whitelist_str = get_secret("WHITELISTED_TENTACLES") or "{}"
                try:
                    whitelist = json.loads(whitelist_str)
                except json.JSONDecodeError:
                    whitelist = {}
                    
                current_hash = self._compute_hash(filepath)
                
                if filename not in whitelist:
                    self.quarantined[filename] = "Unauthorized blacklisted import"
                    print(f"[AST Scanner] Blocked {filename}: Not in whitelist.")
                    return False
                    
                if whitelist[filename] != current_hash:
                    self.quarantined[filename] = "File modified (Hash mismatch)"
                    print(f"[AST Scanner] Blocked {filename}: Hash mismatch!")
                    return False
                    
        except Exception as e:
            print(f"[AST Scanner] Failed to parse {filename}: {e}")
            return False
            
        return True

    def _load_module(self, package_name: str, storage: Dict[str, Any], expected_type: str) -> None:
        """Internal helper to load modules from a given package."""
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            # Package not found, might not be created yet, which is safe to ignore
            return

        if not hasattr(package, "__path__"):
            return

        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                continue
                
            full_module_name = f"{package_name}.{module_name}"
            filepath = os.path.join(package.__path__[0], f"{module_name}.py")
            filename = f"{module_name}.py"
            
            if not self.check_file_security(filepath, filename):
                continue
                
            try:
                module = importlib.import_module(full_module_name)
            except Exception as e:
                print(f"Failed to load module {full_module_name}: {e}")
                continue

            # Load any top-level functions or classes explicitly marked
            for name, obj in inspect.getmembers(module):
                if name.startswith("_"):
                    continue
                
                # Check if it's the base class itself or an abstract class
                if inspect.isclass(obj) and inspect.isabstract(obj):
                    continue

                # Enforce registration via specific attributes
                # e.g., `@tentacle` decorator adding an `is_tentacle = True` attribute
                if hasattr(obj, f"is_{expected_type}"):
                    tool_name = getattr(obj, "tool_name", name)
                    if inspect.isclass(obj):
                        try:
                            storage[tool_name] = obj()
                        except Exception as e:
                            print(f"Failed to instantiate {name}: {e}")
                    else:
                        storage[tool_name] = obj

    def get_tentacle(self, name: str) -> Callable | None:
        """Retrieve a specific Tentacle function by name."""
        return self.tentacles.get(name)

    def get_neuron(self, name: str) -> Any:
        """Retrieve a specific Neuron state machine/class by name."""
        return self.neurons.get(name)

    def get_all_tool_schemas(self) -> list[dict]:
        """Extract Pydantic-based JSON schemas for LLM Function Calling."""
        schemas = []
        for name, obj in self.tentacles.items():
            schemas.append(self._extract_schema(name, obj, "tentacle"))
        for name, obj in self.neurons.items():
            schemas.append(self._extract_schema(name, obj, "neuron"))
        return schemas

    def _extract_schema(self, name: str, obj: Any, tool_type: str) -> dict:
        """
        Extract the JSON schema describing this tool. 
        Expects obj to optionally define:
          - tool_name: str (defaults to its registered name)
          - tool_description: str (defaults to its docstring or a generic message)
          - args_schema: Type[BaseModel] (the Pydantic schema for the input arguments)
        """
        tool_name = getattr(obj, "tool_name", name)
        
        # Determine description from attribute or docstring
        description = getattr(obj, "tool_description", None)
        if not description:
            doc = inspect.getdoc(obj)
            description = doc if doc else f"Executes the {name} {tool_type}."
            
        # Determine parameters schema
        args_schema = getattr(obj, "args_schema", None)
        if args_schema and inspect.isclass(args_schema) and issubclass(args_schema, BaseModel):
            parameters = args_schema.model_json_schema()
        else:
            # Fallback for tools with no explicitly defined args_schema
            parameters = {
                "type": "object",
                "properties": {},
                "additionalProperties": True 
            }
            
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": parameters,
            }
        }


# Global in-memory instance of the Registry
plugin_registry = Registry()
