from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters
import yaml
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
import os
from utils.errors import ConfigurationError, ResourceError
from utils.logging import setup_logger

logger = setup_logger("router")

class Cache:
    def __init__(self, ttl: int = 300, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

class Router:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.clients = {}
        self.sessions = {}
        self.cache = Cache(
            ttl=self.config["router"]["cache"]["ttl"],
            max_size=self.config["router"]["cache"]["max_size"]
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            # Resolve config path relative to the current file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_dir, config_path)
            
            with open(full_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Update server paths to be absolute
            for server_config in config["router"]["servers"].values():
                if "path" in server_config:
                    server_config["path"] = os.path.join("/app", server_config["path"])
                    
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {str(e)}")

    async def initialize(self) -> None:
        """Initialize all server connections"""
        for server_name, server_config in self.config["router"]["servers"].items():
            if server_config["enabled"]:
                try:
                    logger.info(f"Initializing {server_name} server")
                    server_params = StdioServerParameters(
                        command="python",
                        args=[server_config["path"]]
                    )
                    
                    client = await stdio_client(server_params)
                    read, write = await client.__aenter__()
                    session = ClientSession(read, write)
                    await session.__aenter__()
                    await session.initialize()
                    
                    self.sessions[server_name] = session
                    logger.info(f"Successfully initialized {server_name} server")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {server_name}: {str(e)}")
                    raise ResourceError(f"Failed to initialize {server_name}: {str(e)}")

    async def _retry_operation(self, operation, max_attempts: int = None, delay: int = None):
        """Retry an operation with exponential backoff"""
        if max_attempts is None:
            max_attempts = self.config["router"]["retry"]["max_attempts"]
        if delay is None:
            delay = self.config["router"]["retry"]["delay"]

        for attempt in range(max_attempts):
            try:
                return await operation()
            except Exception:
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(delay * (2 ** attempt))

    async def route_request(self, server: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Route a request to the appropriate server"""
        if server not in self.sessions:
            return {"status": "error", "message": f"Server {server} not found"}

        # Generate cache key
        cache_key = f"{server}:{method}:{str(params)}"
        
        # Check cache
        if self.config["router"]["cache"]["enabled"]:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return {"status": "success", "data": cached_result, "source": "cache"}

        try:
            # Call the server method
            result = await self._retry_operation(
                lambda: self.sessions[server].invoke_tool(method, params)
            )

            # Cache successful result
            if self.config["router"]["cache"]["enabled"] and result.get("status") == "success":
                self.cache.set(cache_key, result["data"])

            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def close(self) -> None:
        """Close all server connections"""
        for session in self.sessions.values():
            await session.__aexit__(None, None, None)
