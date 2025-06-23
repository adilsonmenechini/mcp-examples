import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import yaml
from typing import Dict, Any


class KubernetesAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    async def list_resources(self, session: ClientSession) -> None:
        try:
            # List nodes
            nodes_response = await session.invoke_tool("list_nodes")
            print("Nodes:", nodes_response)

            # List pods in configured namespace
            namespace = self.config["kubernetes"].get("namespace", "default")
            pods_response = await session.invoke_tool(
                "list_pods", {"namespace": namespace}
            )
            print("Pods:", pods_response)

            # Get pod logs if any pods exist
            if pods_response.get("pods"):
                for pod in pods_response["pods"]:
                    logs_response = await session.invoke_tool(
                        "get_pod_logs", {"name": pod["name"], "namespace": namespace}
                    )
                    print(f"Logs for {pod['name']}:", logs_response)

        except Exception as e:
            print(f"Error listing resources: {str(e)}")


async def run():
    try:
        agent = KubernetesAgent()
        server_params = StdioServerParameters(
            command="python", args=["kubernetes-agent/mcp_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await agent.list_resources(session)

    except Exception as e:
        print(f"Error running agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run())
