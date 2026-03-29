FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including FFmpeg (CRITICAL for Whisper audio processing)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    alsa-utils \
    sox \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists*

# Copy requirements
COPY requirements.txt .

# Master Fix: Set environment variables to force standard behavior
ENV SETUPTOOLS_USE_DISTUTILS=stdlib
ENV PIP_NO_CACHE_DIR=1

# Critical Build Tools (The "Foundation")
# Lock setuptools to 69.5.1 - this version has pkg_resources
# v70+ removed pkg_resources, breaking openai-whisper
RUN pip install --upgrade pip setuptools==69.5.1 wheel setuptools_scm

# Install Whisper separately WITH --no-build-isolation
# This prevents Whisper from creating an isolated build environment that hides setuptools
RUN pip install --no-build-isolation openai-whisper

# Install the rest of your requirements with --no-build-isolation
# All sub-dependencies will see our upgraded pip/setuptools
RUN pip install --no-build-isolation -r requirements.txt

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
