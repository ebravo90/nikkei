"""
LLM Gateway for Project Nikkei.
Defines base LLMProvider and Tier configurations for intent routing vs complex logic execution.
"""
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from core.security import get_secret


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """
        Generates a response from the LLM.
        """
        pass


class Tier1LLM(LLMProvider):
    """
    Fast/Cheap Model Tier used strictly for intent classification and routing.
    Using gemini-2.5-flash via google-genai SDK.
    """
    def _get_client(self) -> genai.Client:
        api_key = get_secret("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in Keyring.")
        return genai.Client(api_key=api_key)

    def generate(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        print("[Tier1] Routing prompt to gemini-2.5-flash...")
        
        try:
            client = self._get_client()
        except ValueError as e:
            print(f"[Tier1 Error] {e}")
            return {
                "tool_name": None,
                "error": "API Key missing. Configure it in the Dashboard."
            }

        sys_instruct = (
            "You are AgentZero, an intent router. Your job is to select the correct tool "
            "and extract its arguments based on the user prompt. "
            "Respond ONLY with a JSON object in this EXACT format:\n"
            '{"tool_name": "name_of_the_tool", "kwargs": {"arg1": "value", ...}}\n\n'
            "If no tool matches, use tool_name: null."
        )
        if tools:
            sys_instruct += f"\n\nAvailable tools schema:\n{json.dumps(tools, indent=2)}"
            
        config = types.GenerateContentConfig(
            system_instruction=sys_instruct,
            response_mime_type="application/json",
            temperature=0.0
        )
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config
            )
            parsed = json.loads(response.text.strip())
            return {
                "tool_name": parsed.get("tool_name"),
                "kwargs": parsed.get("kwargs", {})
            }
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "resource exhausted" in error_str or "quota" in error_str:
                print("[Tier1 Error] Rate Limit / Quota Exhausted.")
                return {
                    "tool": "sys_cmd",
                    "kwargs": {"command": "echo 'Patrón, se terminaron los 20 pesos del Gemini (API Quota Exhausted). Please wait for the rate limit to reset or configure a fallback LLM.'"}
                }
            print(f"[Tier1 Error] {e}")
            return {
                "tool_name": None,
                "kwargs": {}
            }


class Tier2LLM(LLMProvider):
    """
    Heavy/Smart Model Tier used strictly for coding, complex logic, and grounded research.
    Using gemini-2.5-pro via google-genai SDK, with Google Search Grounding enabled.
    """
    def _get_client(self) -> genai.Client:
        api_key = get_secret("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in Keyring.")
        return genai.Client(api_key=api_key)

    def generate(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        print("[Tier2] Executing logic with gemini-2.5-pro (Web Grounding Active)...")
        
        try:
            client = self._get_client()
        except ValueError as e:
            print(f"[Tier2 Error] {e}")
            return {
                "response": "API Key missing. Configure it in the Dashboard.",
                "status": "error"
            }

        config = types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.2
        )
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=config
            )
            return {
                "response": response.text,
                "status": "success"
            }
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "resource exhausted" in error_str or "quota" in error_str:
                print("[Tier2 Error] Rate Limit / Quota Exhausted.")
                return {
                    "response": "Patrón, se terminaron los 20 pesos del Gemini (API Quota Exhausted). Please wait for the rate limit to reset or configure a fallback LLM.",
                    "status": "error"
                }
            print(f"[Tier2 Error] {e}")
            return {
                "response": str(e),
                "status": "error"
            }
