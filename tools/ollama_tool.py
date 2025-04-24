from mcp_ollama.server import OllamaClient

client = OllamaClient(model="gemma:3b")

def ollama_tool(input_text: str, context: dict) -> str:
    return client.generate(prompt=input_text)
