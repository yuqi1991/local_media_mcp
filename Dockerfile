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

# Create directories
RUN mkdir -p /media /downloads

ENV PYTHONUNBUFFERED=1

# Entry point: start aria2c then MCP server
CMD ["sh", "-c", "aria2c --enable-rpc --rpc-listen-all --rpc-listen-port=6800 --rpc-allow-origin-all --quiet & python -m src.main"]
