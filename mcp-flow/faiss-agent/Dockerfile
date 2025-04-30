FROM mcp-base:latest

# Install system dependencies for FAISS
RUN apt-get update && apt-get install -y \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Install FAISS and other Python dependencies
RUN pip install faiss-cpu \
    numpy \
    pyyaml \
    scikit-learn

# Copy server code
COPY . /app/faiss-agent/

# Set working directory
WORKDIR /app/faiss-agent

# Create volume mount points
VOLUME ["/app/logs", "/app/metrics", "/app/indices"]

# Command to run the server
CMD ["python", "mcp_server.py"]
