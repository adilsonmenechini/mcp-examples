import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


async def run():
    server_params = StdioServerParameters(
        command="python", args=["duckduckgo-agent/mcp_server.py"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            response = await session.invoke_tool(
                "search", {"query": "Python programming", "max_results": 3}
            )
            print("Search Results:", response)


if __name__ == "__main__":
    asyncio.run(run())
