import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import yaml
from typing import Dict, Any


class RouterAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    async def test_server_connections(self, session: ClientSession) -> None:
        """Test connections to all configured servers"""
        for server_name, server_config in self.config["router"]["servers"].items():
            if server_config["enabled"]:
                try:
                    print(f"\nTesting connection to {server_name}...")

                    if server_name == "kubernetes":
                        response = await session.invoke_tool("list_nodes")
                        print(f"Kubernetes nodes: {response}")

                    elif server_name == "neo4j":
                        response = await session.invoke_tool(
                            "query",
                            {"cypher_query": "MATCH (n) RETURN count(n) as count"},
                        )
                        print(f"Neo4j node count: {response}")

                    elif server_name == "faiss":
                        # Test vector operations
                        test_vector = [0.1] * self.config["router"]["integration"][
                            "faiss"
                        ]["dimension"]
                        response = await session.invoke_tool(
                            "add_vectors", {"vectors": [test_vector], "ids": ["test"]}
                        )
                        print(f"FAISS vector added: {response}")

                    elif server_name == "ollama":
                        response = await session.invoke_tool(
                            "generate",
                            {
                                "prompt": "Test prompt",
                                "model_name": self.config["router"]["integration"][
                                    "ollama"
                                ]["default_model"],
                                "max_tokens": 50,
                            },
                        )
                        print(f"Ollama generation: {response}")

                    elif server_name == "duckduckgo":
                        response = await session.invoke_tool(
                            "search", {"query": "test query", "max_results": 1}
                        )
                        print(f"DuckDuckGo search: {response}")

                    print(f"✓ {server_name} connection successful")

                except Exception as e:
                    print(f"✗ {server_name} connection failed: {str(e)}")

    async def test_integration_flow(self, session: ClientSession) -> None:
        """Test the complete integration flow"""
        try:
            print("\nTesting complete integration flow...")

            # Test problem
            test_problem = "What is the best way to implement a cache in Python?"

            print("\n1. Submitting test problem...")
            response = await session.invoke_tool(
                "handle_problem", {"problem_description": test_problem}
            )
            print(f"Initial response: {response}")

            # Test cache
            print("\n2. Testing cache...")
            cached_response = await session.invoke_tool(
                "handle_problem", {"problem_description": test_problem}
            )
            print(f"Cached response: {cached_response}")

            # Test similar problem
            print("\n3. Testing similar problem...")
            similar_problem = "How to implement caching in Python applications?"
            similar_response = await session.invoke_tool(
                "handle_problem", {"problem_description": similar_problem}
            )
            print(f"Similar problem response: {similar_response}")

            print("\n✓ Integration flow test completed")

        except Exception as e:
            print(f"✗ Integration flow test failed: {str(e)}")


async def run():
    try:
        agent = RouterAgent()
        server_params = StdioServerParameters(
            command="python", args=["routers-server/mcp_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Test all server connections
                await agent.test_server_connections(session)

                # Test complete integration flow
                await agent.test_integration_flow(session)

    except Exception as e:
        print(f"Error running agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run())
