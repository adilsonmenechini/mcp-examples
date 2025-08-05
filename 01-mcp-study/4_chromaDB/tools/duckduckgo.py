from ddgs import DDGS
from mcp.server.fastmcp import FastMCP
import json

app = FastMCP()

@app.tool()
def search(query: str) -> dict:
    """
    Realiza uma busca no DuckDuckGo.
    
    Args:
        query (str): A consulta de pesquisa.
    Returns:
        dict: Um dicionário contendo os resultados da pesquisa.
    Raises:
        JsonRpcError: Se ocorrer um erro durante a busca.
    """
    try:
        ddgs = DDGS()
        results = ddgs.text(query, pages=10)
        response = {
            "query": query,
            "results": results
        }
        return response
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")

if __name__ == "__main__":
    app.run()
