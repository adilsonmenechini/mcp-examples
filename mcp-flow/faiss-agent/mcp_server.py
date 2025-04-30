from mcp.server.fastmcp import FastMCP
from core.vector_agent import VectorSearchAgent
from pydantic import BaseModel

mcp = FastMCP("FaissAgent")
agent = VectorSearchAgent(dim=128)


class VectorAddModel(BaseModel):
    vector: list
    id: int


class VectorSearchModel(BaseModel):
    query_vector: list
    k: int = 5


@mcp.tool(name="add_vector", description="Adiciona vetor ao índice FAISS")
def add_vector(data: VectorAddModel):
    try:
        agent.add_vector(data.vector, data.id)
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(name="search_vector", description="Busca vetores similares no índice FAISS")
def search_vector(data: VectorSearchModel):
    try:
        results = agent.search(data.query_vector, data.k)
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("Iniciando Faiss MCP Server")
    mcp.run()
