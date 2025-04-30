from mcp.server.fastmcp import FastMCP
from core.router import Router
from utils.logging import setup_logger
from utils.errors import error_handler

logger = setup_logger("router_mcp_server")

class RouterMCPServer:
    def __init__(self):
        self.mcp = FastMCP("RouterServer")
        self.router = Router()
        self._register_tools()

    def _register_tools(self):
        """Register all routing tools"""

        @self.mcp.tool(name="route_request", description="Route a request to a specific server")
        @error_handler
        async def route_request(server: str, method: str, params: dict) -> dict:
            return await self.router.route_request(server, method, params)

        @self.mcp.tool(name="list_servers", description="List all available servers")
        @error_handler
        async def list_servers() -> dict:
            return {
                "status": "success",
                "data": {
                    name: config
                    for name, config in self.router.config["router"]["servers"].items()
                    if config["enabled"]
                }
            }

    async def initialize(self) -> None:
        """Initialize the router and all server connections"""
        try:
            logger.info("Initializing router server")
            await self.router.initialize()
            logger.info("Router server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize router server: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            logger.info("Cleaning up router server")
            await self.router.close()
            logger.info("Router server cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    def run(self):
        """Start the MCP server"""
        try:
            logger.info("Starting router server")
            self.mcp.run()
        except Exception as e:
            logger.error(f"Router server error: {str(e)}")
            raise
        finally:
            asyncio.run(self.cleanup())

if __name__ == "__main__":
    import asyncio
    
    server = RouterMCPServer()
    asyncio.run(server.initialize())
    server.run()
            logger.error(f"Failed to initialize router server: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            logger.info("Cleaning up router server")
            await self.router.close()
            logger.info("Router server cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    def run(self):
        """Start the MCP server"""
        try:
            logger.info("Starting router server")
            self.mcp.run()
        except Exception as e:
            logger.error(f"Router server error: {str(e)}")
            raise
        finally:
            asyncio.run(self.cleanup())

if __name__ == "__main__":
    import asyncio
    
    server = RouterMCPServer()
    asyncio.run(server.initialize())
    server.run()
            logger.error(f"Failed to initialize router server: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            logger.info("Cleaning up router server")
            await self.router.close()
            logger.info("Router server cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    def run(self):
        """Start the MCP server"""
        try:
            logger.info("Starting router server")
            self.mcp.run()
        except Exception as e:
            logger.error(f"Router server error: {str(e)}")
            raise
        finally:
            asyncio.run(self.cleanup())

if __name__ == "__main__":
    import asyncio
    
    server = RouterMCPServer()
    asyncio.run(server.initialize())
    server.run()
