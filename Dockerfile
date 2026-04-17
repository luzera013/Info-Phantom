# OMNISCIENT ULTIMATE SYSTEM FINAL - Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # System utilities
    curl \
    wget \
    git \
    unzip \
    tar \
    gnupg2 \
    ca-certificates \
    # Web scraping dependencies
    chromium \
    chromium-driver \
    firefox-esr \
    geckodriver \
    # Image processing
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    # Audio processing
    ffmpeg \
    # Other utilities
    htop \
    procps \
    net-tools \
    dnsutils \
    iputils-ping \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r omniscient && \
    useradd -r -g omniscient -d /app -s /bin/bash omniscient

# Set environment variables for Chromium
ENV CHROME_BIN=/usr/bin/chromium \
    CHROME_DRIVER=/usr/bin/chromedriver \
    CHROME_PATH=/usr/bin/chromium \
    GOOGLE_CHROME_SHIM=/usr/bin/chromium \
    DISPLAY=:99

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads /app/temp && \
    chown -R omniscient:omniscient /app

# Set permissions
RUN chmod +x /app/backend/main.py && \
    chmod -R 755 /app

# Switch to non-root user
USER omniscient

# Expose ports
EXPOSE 8000 8080 9050 9051

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Labels
LABEL maintainer="OMNISCIENT Team" \
      version="3.0.0" \
      description="Advanced information collection and analysis system" \
      org.opencontainers.image.source="https://github.com/omniscient/ultimate-system" \
      org.opencontainers.image.licenses="MIT"
