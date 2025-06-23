FROM mcp-base:latest

# Install ollama specific dependencies
RUN pip install ollama \
    pyyaml \
    aiohttp \
    asyncio

# Copy server code
COPY . /app/ollama-agent/

# Set working directory
WORKDIR /app/ollama-agent

# Create volume mount points
VOLUME ["/app/logs", "/app/metrics", "/app/models"]

# Environment variables
ENV OLLAMA_HOST=http://ollama:11434

# Command to run the server
CMD ["python", "mcp_server.py"]
