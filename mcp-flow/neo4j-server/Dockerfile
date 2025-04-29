FROM mcp-base:latest

# Install neo4j specific dependencies
RUN pip install --no-cache-dir \
    neo4j \
    pyyaml \
    retry

# Copy server code
COPY . /app/neo4j-server/

# Set working directory
WORKDIR /app/neo4j-server

# Create volume mount points
VOLUME ["/app/logs", "/app/metrics"]

# Command to run the server
CMD ["python", "mcp_server.py"]
