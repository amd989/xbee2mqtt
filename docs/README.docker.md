# Docker Deployment Guide for xbee2mqtt

This guide explains how to run xbee2mqtt in a Docker container for consistent deployment across any environment.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)
- XBee coordinator radio connected via USB (typically `/dev/ttyUSB0`)
- MQTT broker accessible (can be on same host or remote)

## Docker Hub vs Local Build

There are two ways to run xbee2mqtt with Docker:

### Option 1: Docker Hub (Recommended)

Pull pre-built multi-architecture images from Docker Hub:

```bash
docker pull amd989/xbee2mqtt:latest
```

**Advantages:**
- ✅ No build time - instant deployment
- ✅ Automatically selects correct architecture (amd64, arm64, arm/v7, arm/v6, 386)
- ✅ Always up-to-date with latest stable release
- ✅ Verified builds from CI/CD pipeline

**Use this if:** You want to run the stable version without modifying code.

The default `docker-compose.yml` uses Docker Hub images.

### Option 2: Local Build

Build the Docker image locally from source:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

**Advantages:**
- ✅ Test local code changes
- ✅ Development and debugging
- ✅ Custom modifications

**Use this if:** You're developing or need to modify the code.

The `docker-compose.dev.yml` file is configured for local builds.

## Quick Start

### 1. Configure the Application

Copy the sample configuration and edit it:

```bash
cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml
```

Edit `config/xbee2mqtt.yaml` with your settings:
- Update MQTT broker host/port/credentials
- Configure XBee serial port and baudrate
- Set up topic routes for your XBee devices

### 2. Identify Your XBee Device

Find your XBee serial device:

```bash
# Linux - USB-to-Serial adapter
ls -l /dev/ttyUSB*

# Raspberry Pi - GPIO UART
ls -l /dev/ttyAMA* /dev/serial*

# Check kernel messages for device detection
dmesg | grep tty

# macOS
ls -l /dev/tty.usb*
```

**Common device paths:**
- USB-to-Serial adapter: `/dev/ttyUSB0` (Linux), `/dev/tty.usbserial-*` (macOS)
- Raspberry Pi GPIO UART: `/dev/ttyAMA0` or `/dev/serial0`
- Raspberry Pi connected via USB: `/dev/ttyUSB0` (same as USB adapter)

Update `docker-compose.yml` with your device path. The default is `/dev/ttyUSB0`, but uncomment the Raspberry Pi lines if using GPIO UART.

### 3. Start with Docker Compose

**Using Docker Hub image (recommended):**
```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Using local build (for development):**
```bash
# Build and start
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop
docker-compose -f docker-compose.dev.yml down
```

## Manual Docker Commands

If you prefer not to use Docker Compose:

### Using Docker Hub Image

```bash
# Pull the image
docker pull amd989/xbee2mqtt:latest

# Run the container
docker run -d \
  --name xbee2mqtt \
  --restart unless-stopped \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/var:/app/var \
  amd989/xbee2mqtt:latest
```

### Local Build

```bash
# Build the image
docker build -t xbee2mqtt-local .

# Run the container
docker run -d \
  --name xbee2mqtt \
  --restart unless-stopped \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/var:/app/var \
  xbee2mqtt-local
```

**Windows (PowerShell) with Docker Hub:**
```powershell
docker run -d `
  --name xbee2mqtt `
  --restart unless-stopped `
  --device=/dev/ttyUSB0:/dev/ttyUSB0 `
  -v ${PWD}/config:/app/config:ro `
  -v ${PWD}/var:/app/var `
  amd989/xbee2mqtt:latest
```

### Manage the Container

```bash
# View logs
docker logs -f xbee2mqtt

# Stop container
docker stop xbee2mqtt

# Start container
docker start xbee2mqtt

# Remove container
docker rm -f xbee2mqtt
```

## Configuration

### Serial Device Access

The container needs access to your XBee serial device.

**Option 1: Device mapping (recommended)**

For USB-to-Serial adapters:
```yaml
devices:
  - /dev/ttyUSB0:/dev/ttyUSB0
```

For Raspberry Pi GPIO UART:
```yaml
devices:
  - /dev/ttyAMA0:/dev/ttyAMA0
  # Or use the symlink:
  - /dev/serial0:/dev/serial0
```

You can map multiple devices if needed:
```yaml
devices:
  - /dev/ttyUSB0:/dev/ttyUSB0
  - /dev/ttyAMA0:/dev/ttyAMA0
```

**Option 2: Privileged mode (less secure)**

Only use if device mapping doesn't work:
```yaml
privileged: true
```

**Raspberry Pi Specific Notes:**

1. **Enable UART on Raspberry Pi** (if using GPIO):
   ```bash
   # Edit /boot/config.txt and add:
   enable_uart=1

   # Disable serial console in /boot/cmdline.txt
   # Remove: console=serial0,115200

   # Reboot
   sudo reboot
   ```

2. **Check UART device**:
   ```bash
   # On Raspberry Pi 3/4, /dev/serial0 is symlinked to the correct UART
   ls -l /dev/serial0
   ```

3. **Permissions** (if needed):
   ```bash
   sudo chmod 666 /dev/ttyAMA0
   # or add user to dialout group
   sudo usermod -aG dialout $USER
   ```

### Network Configuration

**For MQTT broker on localhost:**
```yaml
network_mode: host
```

**For remote MQTT broker (default):**
```yaml
network_mode: bridge
# Configure broker IP in config/xbee2mqtt.yaml
```

### Volume Mounts

- `./config:/app/config:ro` - Configuration files (read-only)
- `./var:/app/var` - Logs and PID files (read-write)

### Environment Variables

You can override settings via environment variables:

```yaml
environment:
  - LOGGING_LEVEL=10  # 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR
```

## Troubleshooting

### Serial Port Permission Denied

If you get permission errors accessing the serial port:

**Linux:**
```bash
# Add your user to dialout group
sudo usermod -aG dialout $USER

# Or change device permissions
sudo chmod 666 /dev/ttyUSB0
```

**Docker:**
The container runs as user `xbee` (UID 1000). Ensure the device is accessible.

### Container Won't Start

Check logs:
```bash
docker-compose logs
# or
docker logs xbee2mqtt
```

Common issues:
- Config file not found: Ensure `config/xbee2mqtt.yaml` exists
- Serial device not found: Check device path in docker-compose.yml
- MQTT connection failed: Verify broker host/port in config

### View Container Health

```bash
docker inspect --format='{{.State.Health.Status}}' xbee2mqtt
```

The health check verifies the PID file exists.

## Multi-Platform Support

The Docker image works on:
- Linux (x86_64, ARM, ARM64)
- macOS (via Docker Desktop)
- Windows (via Docker Desktop with WSL2)

For ARM devices (Raspberry Pi, etc.), Docker will automatically build for the correct architecture.

## Production Deployment

For production use:

1. **Use Docker Compose** for easier management
2. **Enable restart policy**: `restart: unless-stopped`
3. **Configure log rotation**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```
4. **Monitor health checks**: Use `docker inspect` or orchestration tools
5. **Backup configuration**: Keep `config/` directory in version control (without secrets)
6. **Use secrets management**: For MQTT credentials, consider Docker secrets or environment variables

## Integration with Other Services

### With Mosquitto MQTT Broker

Example `docker-compose.yml` running both services:

```yaml
version: '3.8'

services:
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data

  xbee2mqtt:
    image: amd989/xbee2mqtt:latest
    container_name: xbee2mqtt
    restart: unless-stopped
    depends_on:
      - mosquitto
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    volumes:
      - ./config:/app/config:ro
      - ./var:/app/var
```

Set MQTT host to `mosquitto` in your config file.

**For local development**, use `build: .` instead of `image: amd989/xbee2mqtt:latest`.

## Testing the Migration

After the Python 2 to Python 3 migration, you should verify everything works:

### 1. Verify Migration (Without Hardware)

Run the verification script to check Python 3 compatibility:

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run verification
python3 verify_migration.py
```

This checks:
- Python version (3.6+)
- All dependencies installed
- No syntax errors
- Modules can be imported
- No Python 2 patterns remain

### 2. Test with Docker (Without Hardware)

Build and test the Docker image:

```bash
# Build the image
docker build -t xbee2mqtt .

# Check if it builds successfully
docker images | grep xbee2mqtt

# Test imports (will fail at runtime without serial device, but tests imports)
docker run --rm xbee2mqtt python3 -c "from libs.config import Config; print('✅ Imports work')"
```

### 3. Dry Run with Mock Configuration

Test that the daemon can load configuration:

```bash
# Create a test config
cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml

# Try to parse config (will fail at serial port, but validates config parsing)
docker run --rm \
  -v $(pwd)/config:/app/config:ro \
  xbee2mqtt \
  python3 -c "from libs.config import Config; c = Config('/app/config/xbee2mqtt.yaml'); print('✅ Config loads OK')"
```

### 4. Integration Test (With Hardware)

Once you have XBee hardware connected:

```bash
# Start in foreground to watch logs
docker-compose up

# Watch for:
# - "Connecting to Xbee" message
# - "Connected to MQTT broker" message
# - No Python errors or exceptions

# If successful, run in background
docker-compose down
docker-compose up -d
```

### 5. Monitor Runtime

After starting, monitor for issues:

```bash
# Check logs for errors
docker-compose logs -f

# Check container is running
docker-compose ps

# Check health status
docker inspect --format='{{.State.Health.Status}}' xbee2mqtt
```

### Expected Behavior

A successful migration should show:
- ✅ Container starts without Python errors
- ✅ Connects to XBee serial device
- ✅ Connects to MQTT broker
- ✅ Receives and publishes XBee messages
- ✅ Responds to MQTT commands

### Troubleshooting Migration Issues

If you encounter Python errors:

1. **ImportError**: Check dependencies in requirements.txt
2. **SyntaxError**: Run `python3 verify_migration.py` to find issues
3. **AttributeError**: May indicate Python 2/3 incompatibility - check the error line
4. **UnicodeDecodeError**: Likely bytes/string handling - report the issue

## Updating

### Updating Docker Hub Image

To update to the latest version from Docker Hub:

```bash
# Pull latest image
docker pull amd989/xbee2mqtt:latest

# Restart with new image
docker-compose down
docker-compose up -d
```

The latest image is automatically built from the master branch via GitHub Actions.

### Updating Local Build

To update with local changes:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d
```
