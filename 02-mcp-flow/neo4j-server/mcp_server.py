from mcp.server.fastmcp import FastMCP
from core.graph_agent import GraphAgent
from core.vector_agent import VectorAgent
from pydantic import BaseModel

mcp = FastMCP("Neo4jServer")

graph_agent = GraphAgent()
vector_agent = VectorAgent(dim=128)


class QueryModel(BaseModel):
    cypher_query: str


class VectorAddModel(BaseModel):
    vector: list
    id: int


class VectorSearchModel(BaseModel):
    query_vector: list
    k: int = 5


@mcp.tool(name="query_graph", description="Executa consulta Cypher no Neo4j")
def query_graph(data: QueryModel):
    try:
        result = graph_agent.query(data.cypher_query)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(name="add_vector", description="Adiciona vetor ao índice FAISS")
def add_vector(data: VectorAddModel):
    try:
        vector_agent.add_vector(data.vector, data.id)
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(name="search_vector", description="Busca vetores similares no índice FAISS")
def search_vector(data: VectorSearchModel):
    try:
        results = vector_agent.search(data.query_vector, data.k)
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("Iniciando Neo4j MCP Server")
    mcp.run()
