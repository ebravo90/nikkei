import webbrowser
import urllib.parse
from pydantic import BaseModel, Field
from typing import Dict, Any

from tentacles.base import Tentacle


class BrowserArgs(BaseModel):
    action: str = Field(..., description="The specific browser action to execute.", json_schema_extra={"enum": ["open_url", "search_google", "search_youtube"]})
    query_or_url: str = Field(..., description="Either an explicit 'https://' URL or a natural language search query depending on the action.")


class BrowserTentacle(Tentacle):
    """
    Opens web protocols safely using the native OS browser handler.
    Use this to execute visual side-effects like "play a video" or "open a tab".
    Does not extract content (for data extraction, build a separate web-scraper tentacle).
    """
    
    tool_name = "browser"
    tool_description = "Opens websites, performs Google searches, and opens YouTube functionally within the host system's default browser UI."
    args_schema = BrowserArgs
    requires_approval = True

    def _execute(self, action: str, query_or_url: str, **kwargs) -> Dict[str, Any]:
        """Executes the specified browser opening operation."""
        try:
            if action == "open_url":
                if not query_or_url.startswith(('http://', 'https://', 'file://')):
                    query_or_url = 'https://' + query_or_url
                    
                webbrowser.open(query_or_url)
                return {"status": "success", "result": f"Successfully opened URL: {query_or_url}"}
                
            elif action == "search_google":
                encoded_query = urllib.parse.quote_plus(query_or_url)
                target_url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(target_url)
                return {"status": "success", "result": f"Successfully launched Google search for: '{query_or_url}'"}
                
            elif action == "search_youtube":
                encoded_query = urllib.parse.quote_plus(query_or_url)
                target_url = f"https://www.youtube.com/results?search_query={encoded_query}"
                webbrowser.open(target_url)
                return {"status": "success", "result": f"Successfully launched YouTube search for: '{query_or_url}'"}
                
            else:
                return {"status": "error", "error": f"Unsupported browser action '{action}'."}
                
        except Exception as e:
            return {"status": "error", "error": f"Error executing browser operation '{action}': {str(e)}"}
