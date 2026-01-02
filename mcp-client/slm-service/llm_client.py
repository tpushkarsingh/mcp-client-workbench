import ollama
from typing import List, Dict, Any

class LLMClient:
    def __init__(self, model: str = "functiongemma:latest"):
        self.model = model
        self.client = ollama.Client(host='http://localhost:11434')

    async def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends a chat request to Ollama.
        """
        # Convert MCP tools to Ollama tools format if necessary
        # Ollama expects: { "type": "function", "function": { "name": ..., "description": ..., "parameters": ... } }
        ollama_tools = []
        if tools:
            for tool in tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {})
                    }
                })

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=ollama_tools if ollama_tools else None,
            )
            return response['message']
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            raise e
