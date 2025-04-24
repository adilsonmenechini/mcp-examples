import logging
from mcp.server import FastMCP

app = FastMCP("MCP Example")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
