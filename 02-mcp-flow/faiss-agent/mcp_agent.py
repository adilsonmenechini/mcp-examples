import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import yaml
import numpy as np
from typing import Dict, Any
import os
import time


class FaissAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self._ensure_backup_dir()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    def _ensure_backup_dir(self) -> None:
        backup_path = self.config["faiss"]["backup_path"]
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

    async def add_test_vectors(self, session: ClientSession) -> None:
        try:
            # Generate some test vectors
            dim = self.config["faiss"]["dimension"]
            num_vectors = 10
            vectors = np.random.rand(num_vectors, dim).tolist()
            ids = list(range(num_vectors))

            # Add vectors in batches
            batch_size = self.config["faiss"]["batch_size"]
            for i in range(0, len(vectors), batch_size):
                batch_vectors = vectors[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                await session.invoke_tool(
                    "add_vectors", {"vectors": batch_vectors, "ids": batch_ids}
                )
                print(f"Added vectors batch {i // batch_size + 1}")

        except Exception as e:
            print(f"Error adding test vectors: {str(e)}")

    async def test_search(self, session: ClientSession) -> None:
        try:
            # Generate a test query vector
            dim = self.config["faiss"]["dimension"]
            query_vector = np.random.rand(dim).tolist()

            # Search with the query vector
            response = await session.invoke_tool(
                "search", {"query_vector": query_vector, "k": 5}
            )
            print("Search results:", response)

        except Exception as e:
            print(f"Error performing search: {str(e)}")

    async def manage_index(self, session: ClientSession) -> None:
        try:
            # Save index
            index_path = self.config["faiss"]["index_path"]
            await session.invoke_tool("save", {"path": index_path})
            print(f"Index saved to {index_path}")

            # Create backup with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                self.config["faiss"]["backup_path"], f"index_backup_{timestamp}"
            )
            await session.invoke_tool("save", {"path": backup_path})
            print(f"Backup created at {backup_path}")

        except Exception as e:
            print(f"Error managing index: {str(e)}")


async def run():
    try:
        agent = FaissAgent()
        server_params = StdioServerParameters(
            command="python", args=["faiss-agent/mcp_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Add test vectors
                await agent.add_test_vectors(session)

                # Test search functionality
                await agent.test_search(session)

                # Save index and create backup
                await agent.manage_index(session)

    except Exception as e:
        print(f"Error running agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run())
