FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    alsa-utils \
    sox \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Upgrade pip and install build tools BEFORE requirements
# This fixes: ModuleNotFoundError: No module named 'pkg_resources'
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/models data/vector_db data/metrics data/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV EDGE_MODE=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose API port
EXPOSE 8000

# Run API server
CMD ["python3", "api_server.py"]
