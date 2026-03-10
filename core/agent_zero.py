"""
Agente Cero (The Router) for Project Nikkei.
Powered by Tier 1. It receives the natural language prompt, uses Function Calling 
against the loaded Registry, and routes the payload to either a Tentacle or a Neuron.
"""
from typing import Dict, Any

from pydantic import ValidationError

from core.registry import plugin_registry
from core.llm_gateway import Tier1LLM


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

        return {"status": "unmatched", "tool": tool_name, "message": "Tool not found in registry."}
