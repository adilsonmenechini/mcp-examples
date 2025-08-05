from mcp.server.fastmcp import FastMCP
from core.search_agent import DuckDuckGoAgent
from pydantic import BaseModel

mcp = FastMCP("DuckDuckGoAgent")
search_agent = DuckDuckGoAgent()


class SearchModel(BaseModel):
    query: str
    max_results: int = 5


@mcp.tool(name="search", description="Busca na web usando DuckDuckGo")
def search(data: SearchModel):
    try:
        results = search_agent.search(data.query, data.max_results)
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("Iniciando DuckDuckGo MCP Server")
    mcp.run()
