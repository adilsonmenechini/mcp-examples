FROM mcp-base:latest

# Install ollama specific dependencies
RUN pip install pyyaml \
    aiohttp \
    asyncio \
    mcp

# Copy server code
COPY . /app/ollama-agent/

# Set working directory
WORKDIR /app/ollama-agent

# Create volume mount points
VOLUME ["/app/logs", "/app/metrics", "/app/models"]

# Command to run the server
CMD ["python", "mcp_server.py"]
