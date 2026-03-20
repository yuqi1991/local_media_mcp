FROM python:3.11-slim

# Install aria2
RUN apt-get update && apt-get install -y aria2 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config.yaml .

# Create directories and config directory
RUN mkdir -p /media/jav/JAV_output /downloads /media/jav /app/config

ENV PYTHONUNBUFFERED=1
ENV ARIA2_RPC_SECRET=${ARIA2_RPC_SECRET:-}
ENV MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-}

# Entry point: start aria2c then MCP server
CMD ["sh", "-c", "aria2c --conf-path=/app/config/aria2.conf $([ -n \"$ARIA2_RPC_SECRET\" ] && echo --rpc-secret=$ARIA2_RPC_SECRET) --quiet & python -m src.main"]
