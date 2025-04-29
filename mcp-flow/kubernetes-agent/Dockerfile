FROM mcp-base:latest

# Install kubernetes specific dependencies
RUN pip install --no-cache-dir \
    kubernetes \
    pyyaml \
    requests

# Copy server code
COPY . /app/kubernetes-agent/

# Set working directory
WORKDIR /app/kubernetes-agent

# Create volume mount points
VOLUME ["/app/logs", "/app/metrics", "/root/.kube"]

# Command to run the server
CMD ["python", "mcp_server.py"]
