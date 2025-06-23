from mcp.server.fastmcp import FastMCP
from .config import ConfigHandler
from .logging import setup_logger
from .cache import JSONCache
from typing import Dict, Any, Optional
import asyncio


class BaseMCPServer:
    def __init__(self, server_name: str, config_path: str = None):
        # Initialize configuration
        self.config = ConfigHandler(server_name, config_path)

        # Setup logging
        self.logger = setup_logger("server", server_name, self.config.config)

        # Initialize MCP server
        self.mcp = FastMCP(server_name)

        # Initialize cache if enabled
        cache_config = self.config.get("cache", {})
        if cache_config.get("enabled", True):
            self.cache = JSONCache(
                ttl=cache_config.get("ttl", 300),
                max_size=cache_config.get("max_size", 1000),
            )
        else:
            self.cache = None

    async def initialize(self) -> None:
        """Initialize server resources"""
        try:
            # Start cache cleanup if enabled
            if self.cache:
                await self.cache.start_cleanup()

            # Register common tools
            self._register_common_tools()

            # Register server-specific tools
            await self.register_tools()

            self.logger.info("Server initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize server: {str(e)}")
            raise

    def _register_common_tools(self) -> None:
        """Register common tools available to all servers"""

        @self.mcp.tool(name="get_config", description="Get server configuration")
        async def get_config(key: str = None) -> Dict:
            """Get server configuration"""
            try:
                if key:
                    value = self.config.get(key)
                    return {"status": "success", "data": {key: value}}
                else:
                    return {"status": "success", "data": self.config.config}
            except Exception as e:
                self.logger.error(f"Failed to get config: {str(e)}")
                return {"status": "error", "message": str(e)}

        @self.mcp.tool(name="update_config", description="Update server configuration")
        async def update_config(updates: Dict[str, Any]) -> Dict:
            """Update server configuration"""
            try:
                self.config.update(updates)
                return {"status": "success", "message": "Configuration updated"}
            except Exception as e:
                self.logger.error(f"Failed to update config: {str(e)}")
                return {"status": "error", "message": str(e)}

        @self.mcp.tool(name="clear_cache", description="Clear server cache")
        async def clear_cache() -> Dict:
            """Clear server cache"""
            try:
                if self.cache:
                    await self.cache.clear()
                    return {"status": "success", "message": "Cache cleared"}
                else:
                    return {"status": "error", "message": "Cache is not enabled"}
            except Exception as e:
                self.logger.error(f"Failed to clear cache: {str(e)}")
                return {"status": "error", "message": str(e)}

        @self.mcp.tool(name="get_server_info", description="Get server information")
        async def get_server_info() -> Dict:
            """Get server information and status"""
            try:
                info = {
                    "name": self.mcp.name,
                    "config_path": self.config.config_path,
                    "cache_enabled": self.cache is not None,
                    "tools": [
                        {"name": tool.name, "description": tool.description}
                        for tool in self.mcp.tools
                    ],
                }
                if self.cache:
                    info["cache"] = {
                        "size": len(self.cache.cache),
                        "max_size": self.cache.max_size,
                        "ttl": self.cache.ttl,
                    }
                return {"status": "success", "data": info}
            except Exception as e:
                self.logger.error(f"Failed to get server info: {str(e)}")
                return {"status": "error", "message": str(e)}

    async def register_tools(self) -> None:
        """
        Register server-specific tools.
        Should be implemented by each server.
        """
        raise NotImplementedError("Servers must implement register_tools()")

    def run(self) -> None:
        """Start the MCP server"""
        try:
            # Initialize server
            asyncio.run(self.initialize())

            self.logger.info(f"Starting {self.mcp.name}")
            self.mcp.run()
        except Exception as e:
            self.logger.error(f"Server error: {str(e)}")
            raise
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Cleanup server resources"""
        try:
            if self.cache:
                asyncio.run(self.cache.stop_cleanup())
            self.logger.info("Server shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    @staticmethod
    def format_response(result: Any, error: Optional[str] = None) -> Dict:
        """Format response in a consistent way"""
        if error:
            return {"status": "error", "message": error}
        else:
            return {"status": "success", "data": result}
