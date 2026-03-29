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

# Expert fix for openai-whisper pkg_resources issue
# The problem: openai-whisper's setup.py imports pkg_resources at module level
# Solution: Install dependency chain explicitly, then force wheel installation

# Step 1: Upgrade pip and core tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Step 2: Force install setuptools into Python's default import path
RUN pip install --force-reinstall --no-cache-dir --no-deps 'setuptools>=67.0.0'

# Step 3: Install openai-whisper FIRST, using only pre-built wheels (avoids setup.py build)
# This prevents the ModuleNotFoundError in the subprocess
RUN pip install --no-cache-dir --only-binary :all: openai-whisper || pip install --no-cache-dir openai-whisper

# Step 4: Install remaining dependencies
# By this point, setuptools is properly initialized and in Python path
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
