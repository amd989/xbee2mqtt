FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    pyyaml \
    pyserial \
    paho-mqtt \
    parse \
    xbee \
    pytest

# Create config directory and volume mount point
RUN mkdir -p /app/config /app/var

# Volume for configuration and logs
VOLUME ["/app/config", "/app/var"]

# Run as non-root user
RUN useradd -m -u 1000 xbee && \
    chown -R xbee:xbee /app
USER xbee

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD test -f /app/var/xbee2mqtt.pid || exit 1

# Foreground mode - Docker will handle process management
CMD ["python", "-u", "xbee2mqtt.py", "start"]
