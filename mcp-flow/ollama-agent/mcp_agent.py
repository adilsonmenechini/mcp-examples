import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import yaml
from typing import Dict, Any


class OllamaAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    async def test_generation(self, session: ClientSession) -> None:
        try:
            # Test with different models
            for model_config in self.config["ollama"]["models"]:
                model_name = model_config["name"]
                print(f"\nTesting model: {model_name}")

                # Test standard generation
                prompt = f"Write a short poem about artificial intelligence using {model_name}"
                response = await session.invoke_tool(
                    "generate",
                    {
                        "prompt": prompt,
                        "model_name": model_name,
                        "max_tokens": model_config["max_tokens"],
                    },
                )
                print(f"Standard generation response:\n{response}")

                # Test streaming generation
                if self.config["ollama"]["stream"]:
                    print("\nStreaming generation:")
                    async for chunk in await session.invoke_tool(
                        "generate_stream",
                        {
                            "prompt": "Explain what makes this model special",
                            "model_name": model_name,
                            "max_tokens": model_config["max_tokens"],
                        },
                    ):
                        print(chunk, end="", flush=True)
                    print()  # New line after streaming

        except Exception as e:
            print(f"Error in test_generation: {str(e)}")

    async def manage_models(self, session: ClientSession) -> None:
        try:
            # List available models
            models = await session.invoke_tool("list_models")
            print("\nAvailable models:", models)

            # Check if required models are available
            required_models = [m["name"] for m in self.config["ollama"]["models"]]
            for model in required_models:
                if model not in models:
                    print(f"Warning: Required model '{model}' is not available")

        except Exception as e:
            print(f"Error managing models: {str(e)}")


async def run():
    try:
        agent = OllamaAgent()
        server_params = StdioServerParameters(
            command="python", args=["ollama-agent/mcp_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Check available models
                await agent.manage_models(session)

                # Test generation capabilities
                await agent.test_generation(session)

    except Exception as e:
        print(f"Error running agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run())
