import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


class VectorAgent:
    def __init__(self, dim: int = 128):
        self.server_params = StdioServerParameters(
            command="python",
            args=["faiss-agent/mcp_server.py"]
        )
        self.dim = dim
        self._session = None

    async def _ensure_session(self):
        if self._session is None:
            read, write = await stdio_client(self.server_params).__aenter__()
            self._session = ClientSession(read, write)
            await self._session.initialize()

    async def add_vector(self, vector: list, id: int) -> None:
        """Add a single vector to the index"""
        try:
            await self._ensure_session()
            result = await self._session.invoke_tool(
                "add_vector",
                {"vector": vector, "id": id}
            )
            if "error" in result:
                raise Exception(result["error"])
        except Exception as e:
            raise Exception(f"Failed to add vector: {str(e)}")

    async def search(self, query_vector: list, k: int = 5) -> list:
        """Search for similar vectors"""
        try:
            await self._ensure_session()
            result = await self._session.invoke_tool(
                "search_vector",
                {"query_vector": query_vector, "k": k}
            )
            if "error" in result:
                raise Exception(result["error"])
            return result["results"]
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    async def close(self):
        if self._session:
            await self._session.close()
