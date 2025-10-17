FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install Python dependencies from requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create config directory and volume mount point
RUN mkdir -p /app/config /app/var

# Volume for configuration and logs
VOLUME ["/app/config", "/app/var"]

# Run as non-root user with serial port access
# Add user to dialout group for serial port permissions
RUN useradd -m -u 1000 xbee && \
    usermod -a -G dialout xbee && \
    chown -R xbee:xbee /app
USER xbee

# Run in foreground mode - Docker will handle process management
CMD ["python", "-u", "docker-entrypoint.py"]
