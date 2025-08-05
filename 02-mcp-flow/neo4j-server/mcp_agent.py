import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import yaml
from typing import Dict, Any, List


class Neo4jAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    async def execute_queries(self, session: ClientSession) -> None:
        try:
            # Example queries
            queries = [
                "MATCH (n) RETURN count(n) as count",  # Count all nodes
                "MATCH (n)-[r]-() RETURN count(r) as relationships",  # Count relationships
                "MATCH (n) RETURN DISTINCT labels(n) as labels",  # Get all labels
            ]

            for query in queries:
                try:
                    response = await session.invoke_tool(
                        "query", {"cypher_query": query}
                    )
                    print(f"Query result for '{query}':", response)
                except Exception as e:
                    print(f"Error executing query '{query}': {str(e)}")
                    continue  # Continue with next query even if one fails

        except Exception as e:
            print(f"Error in execute_queries: {str(e)}")

    async def write_data(self, session: ClientSession, data: List[Dict]) -> None:
        try:
            for item in data:
                query = """
                CREATE (n:Example {
                    id: $id,
                    name: $name
                })
                """
                params = {"cypher_query": query, "params": item}
                await session.invoke_tool("write_transaction", params)
                print(f"Created node with data: {item}")

        except Exception as e:
            print(f"Error writing data: {str(e)}")


async def run():
    try:
        agent = Neo4jAgent()
        server_params = StdioServerParameters(
            command="python", args=["neo4j-server/mcp_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Execute example queries
                await agent.execute_queries(session)

                # Example data write
                example_data = [
                    {"id": 1, "name": "Example1"},
                    {"id": 2, "name": "Example2"},
                ]
                await agent.write_data(session, example_data)

    except Exception as e:
        print(f"Error running agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run())
