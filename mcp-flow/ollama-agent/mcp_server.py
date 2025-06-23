import os
import yaml
from mcp.server.fastmcp import FastMCP
from core.llm_handler import LLM_Agent
from pydantic import BaseModel
from utils.errors import error_handler, MCPError, ConfigurationError
from utils.logging import setup_logger

logger = setup_logger("ollama_mcp_server")

class PromptModel(BaseModel):
    prompt: str
    max_tokens: int = 100

class OllamaMCPServer:
    def __init__(self):
        self.mcp = FastMCP("OllamaAgent")
        self.config = self._load_config()
        self.agent = None
        self._register_tools()

    def _load_config(self) -> dict:
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(base_dir, "routers-server", "config.yaml")
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {str(e)}")

    def _register_tools(self):
        @self.mcp.tool(name="generate_text", description="Generate text using Ollama model")
        @error_handler
        async def generate_text(data: PromptModel):
            if not self.agent:
                raise MCPError("Ollama agent not initialized")
            try:
                text = await self.agent.generate(
                    data.prompt,
                    max_tokens=data.max_tokens
                )
                return {"status": "success", "data": {"text": text}}
            except Exception as e:
                logger.error(f"Text generation failed: {str(e)}")
                raise MCPError(f"Text generation failed: {str(e)}")

    async def initialize(self) -> None:
        """Initialize the Ollama agent"""
        try:
            logger.info("Initializing Ollama agent")
            self.agent = LLM_Agent(
                model_name=self.config["router"]["integration"]["ollama"]["default_model"],
                host="http://localhost:11434"
            )
            logger.info("Ollama agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama agent: {str(e)}")
            raise MCPError(f"Failed to initialize Ollama agent: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            logger.info("Cleaning up Ollama agent")
            if self.agent:
                await self.agent.close()
            logger.info("Ollama agent cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    def run(self):
        """Start the MCP server"""
        try:
            logger.info("Starting Ollama MCP server")
            self.mcp.run()
        except Exception as e:
            logger.error(f"Ollama MCP server error: {str(e)}")
            raise
        finally:
            import asyncio
            asyncio.run(self.cleanup())

if __name__ == "__main__":
    import asyncio
    
    server = OllamaMCPServer()
    asyncio.run(server.initialize())
    server.run()
