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

# Master fix for pkg_resources: openai-whisper setuptools issue
# Step 1: Upgrade and ensure pip is modern
RUN pip install --no-cache-dir --upgrade pip

# Step 2: Install setuptools, wheel, and setuptools_scm (provides pkg_resources)
RUN pip install --no-cache-dir --upgrade 'setuptools>=67.0.0' wheel setuptools_scm

# Step 3: Use stdlib distutils and install requirements  
# Environment variable helps packages avoid setuptools import issues
ENV SETUPTOOLS_USE_DISTUTILS=stdlib

# Step 4: Install all Python dependencies with no isolation (accesses system setuptools)
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

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
