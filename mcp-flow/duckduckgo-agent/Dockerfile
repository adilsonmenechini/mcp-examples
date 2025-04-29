FROM mcp-base:latest

# Install duckduckgo specific dependencies
RUN pip install --no-cache-dir \
    duckduckgo-search \
    pyyaml \
    aiohttp \
    beautifulsoup4 \
    html2text

# Copy server code
COPY . /app/duckduckgo-agent/

# Set working directory
WORKDIR /app/duckduckgo-agent

# Create volume mount points
VOLUME ["/app/logs", "/app/metrics", "/app/cache"]

# Command to run the server
CMD ["python", "mcp_server.py"]
