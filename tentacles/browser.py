import webbrowser
import urllib.parse
from pydantic import Field

from tentacles.base import Tentacle


class BrowserTentacle(Tentacle):
    """
    Opens web protocols safely using the native OS browser handler.
    Use this to execute visual side-effects like "play a video" or "open a tab".
    Does not extract content (for data extraction, build a separate web-scraper tentacle).
    """
    
    name = "browser"
    description = "Opens websites, performs Google searches, and opens YouTube functionally within the host system's default browser UI."
    version = "1.0.0"

    parameters = {
        "action": Field(
            description="The specific browser action to execute.",
            enum=["open_url", "search_google", "search_youtube"]
        ),
        "query_or_url": Field(
            description="Either an explicit 'https://' URL or a natural language search query depending on the action."
        )
    }

    def execute(self, action: str, query_or_url: str, **kwargs) -> str:
        """Executes the specified browser opening operation."""
        try:
            if action == "open_url":
                # Ensure a scheme is present for explicit URL opening
                if not query_or_url.startswith(('http://', 'https://', 'file://')):
                    query_or_url = 'https://' + query_or_url
                    
                webbrowser.open(query_or_url)
                return f"Successfully opened URL: {query_or_url}"
                
            elif action == "search_google":
                encoded_query = urllib.parse.quote_plus(query_or_url)
                target_url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(target_url)
                return f"Successfully launched Google search for: '{query_or_url}'"
                
            elif action == "search_youtube":
                encoded_query = urllib.parse.quote_plus(query_or_url)
                target_url = f"https://www.youtube.com/results?search_query={encoded_query}"
                webbrowser.open(target_url)
                return f"Successfully launched YouTube search for: '{query_or_url}'"
                
            else:
                return f"Error: Unsupported browser action '{action}'."
                
        except Exception as e:
            return f"Error executing browser operation '{action}': {str(e)}"
