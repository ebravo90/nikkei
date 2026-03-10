"""
Web Search Sucker for Project Nikkei.
Uses Tier2LLM (Gemini 2.5 Pro) with Google Search Grounding to extract structured JSON data from the live web.
"""
import json
from typing import Any, Dict
from tentacles.base import Sucker
from core.llm_gateway import Tier2LLM

class GeminiSearchSucker(Sucker):
    """
    Extracts structured data from the live web using Gemini Search Grounding.
    """
    def __init__(self):
        self.llm = Tier2LLM()

    def extract(self, query: str) -> Any:
        """
        Prompts the grounded LLM to search for the query and forces a JSON return format.
        """
        print(f"[GeminiSearchSucker] Extracting data from live web for query: {query}")
        
        # We enforce JSON output directly in the prompt for the grounded model
        json_prompt = f"""
        {query}
        
        CRITICAL INSTRUCTION: You must return the extracted data STRICTLY as a valid JSON object or array. 
        Do not include markdown formatting like ```json or any conversational text. 
        Only output the raw JSON string.
        """
        
        try:
            # We assume Tier2LLM is configured with the `google_search` tool enabled
            result = self.llm.generate(json_prompt)
            raw_response = result.get("response", "{}")
            
            # Clean up potential markdown blocks if the LLM disobeyed
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:]
            if raw_response.startswith("```"):
                raw_response = raw_response[3:]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]
                
            return json.loads(raw_response.strip())
        except json.JSONDecodeError as e:
            print(f"[GeminiSearchSucker] Failed to parse JSON from LLM: {e}")
            return {"error": "Failed to extract structured JSON", "raw": raw_response}
        except Exception as e:
            print(f"[GeminiSearchSucker] Extraction failed: {e}")
            return {"error": str(e)}
