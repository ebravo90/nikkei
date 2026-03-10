"""
Agente Cero (The Router) for Project Nikkei.
Powered by Tier 1. It receives the natural language prompt, uses Function Calling 
against the loaded Registry, and routes the payload to either a Tentacle or a Neuron.
"""
import uuid
from typing import Dict, Any

from pydantic import ValidationError

from core.registry import plugin_registry
from core.llm_gateway import Tier1LLM
from core.security import SecurityApprovalRequired


class AgentZero:
    def __init__(self):
        self.router_llm = Tier1LLM()
        
    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Retrieves JSON schemas for Function Calling, sends user prompt to Tier1,
        and parses routing decision to activate target plugins natively.
        Validates LLM-generated arguments against the tool's Pydantic schema.
        """
        # 1. Fetch JSON definitions of tools loaded in registry
        schemas = plugin_registry.get_all_tool_schemas()
        
        # 2. Invoke Tier 1 LLM with Function Calling payload
        routing_decision = self.router_llm.generate(prompt, tools=schemas)
        
        tool_name = routing_decision.get("tool_name")
        kwargs = routing_decision.get("kwargs", {})
        
        if not tool_name:
            return {"status": "unmatched", "message": "LLM did not invoke any function."}
            
        # 3. Route execution to appropriate Tentacle or Neuron
        tentacle = plugin_registry.get_tentacle(tool_name)
        if tentacle:
            # Atomic Actions (Single-Shot)
            try:
                # 3a. Validate arguments if the tentacle has an args_schema
                if hasattr(tentacle, "args_schema") and tentacle.args_schema:
                    try:
                        validated_args = tentacle.args_schema(**kwargs)
                        # Depending on execution mechanism, we might pass the model or its dict
                        kwargs = validated_args.model_dump()
                    except ValidationError as ve:
                        # LLM hallucinated invalid arguments
                        return {
                            "status": "validation_error",
                            "tool": tool_name,
                            "error": ve.errors(),
                            "original_kwargs": kwargs
                        }
                        
                # 3b. Execute verified arguments
                # Note: We assume tentacle is our Tentacle base class instance, so we call .execute()
                # But since we previously mapped it to Callable, let's gracefully call either __call__ or execute
                if hasattr(tentacle, "execute"):
                    result = tentacle.execute(**kwargs)
                else:
                    result = tentacle(**kwargs)
                    
                return {
                    "status": "routed_to_tentacle",
                    "tool": tool_name,
                    "args": kwargs,
                    "result": result
                }
            except SecurityApprovalRequired:
                return {
                    "status": "pending_approval",
                    "tool": tool_name,
                    "kwargs": kwargs,
                    "message": f"Security Alert: Executing {tool_name}. Do you approve?"
                }
            except Exception as e:
                return {"status": "tentacle_error", "tool": tool_name, "error": str(e)}
                
        neuron = plugin_registry.get_neuron(tool_name)
        if neuron:
            # Complex Orchestrators / State Machines
            try:
                # Validate Neuron Arguments
                if hasattr(neuron, "args_schema") and neuron.args_schema:
                    try:
                        validated_args = neuron.args_schema(**kwargs)
                        kwargs = validated_args.model_dump()
                    except ValidationError as ve:
                        return {
                            "status": "validation_error",
                            "tool": tool_name,
                            "error": ve.errors(),
                            "original_kwargs": kwargs
                        }
                        
                # Mock initiation of complex workflow logic
                return {
                    "status": "routed_to_neuron",
                    "tool": tool_name,
                    "args": kwargs,
                    "details": "Initiating complex state machine..."
                }
            except Exception as e:
                return {"status": "neuron_error", "tool": tool_name, "error": str(e)}


    def process_direct(self, tool_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Bypass LLM parsing and directly invoke a known tool (e.g., after approval)"""
        import core.security
        
        # Generate a thread-safe single-use bypass token
        bypass_token = str(uuid.uuid4())
        core.security.approved_action_tokens.add(bypass_token)

        try:
            tentacle = plugin_registry.get_tentacle(tool_name)
            if tentacle:
                # Inject the bypass token into the execution payload
                kwargs["bypass_token"] = bypass_token
                
                if hasattr(tentacle, "execute"):
                    result = tentacle.execute(**kwargs)
                else:
                    result = tentacle(**kwargs)
                return {"status": "routed_to_tentacle", "tool": tool_name, "args": kwargs, "result": result}
            return {"status": "unmatched"}
        except Exception as e:
            # Revert the token if execution failed before consuming it
            core.security.approved_action_tokens.discard(bypass_token)
            return {"status": "tentacle_error", "tool": tool_name, "error": str(e)}
