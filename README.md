# xbee2mqtt

[![Docker Pulls](https://img.shields.io/docker/pulls/amd989/xbee2mqtt)](https://hub.docker.com/r/amd989/xbee2mqtt)
[![Docker Image Size](https://img.shields.io/docker/image-size/amd989/xbee2mqtt/latest)](https://hub.docker.com/r/amd989/xbee2mqtt)
[![Build Status](https://img.shields.io/github/actions/workflow/status/amd989/xbee2mqtt/docker-build.yml?branch=master)](https://github.com/amd989/xbee2mqtt/actions)

A Python 3 daemon that bridges XBee ZigBee radios to MQTT brokers. It monitors a coordinator XBee connected to a serial port, translates radio messages to MQTT topics, and enables remote control of XBee digital I/O pins through MQTT commands.

From version 0.3 it also supports setting digital pins LOW or HIGH on remote radios.

**Key requirements:**
- The XBee radio **must** be configured in API mode (not transparent mode)
- Python 3.6+ (migrated from Python 2.7)

## Quick Start with Docker (Recommended)

The easiest way to run xbee2mqtt is using Docker. Pre-built images available for all major architectures!

### Using Docker Hub (Recommended)

```bash
# Pull the latest image (automatically selects your architecture)
docker pull amd989/xbee2mqtt:latest

# Or use docker-compose (see docker-compose.yml)
docker-compose up -d
```

**Supported architectures:**
- `linux/amd64` - x86 64-bit (PCs, servers, cloud)
- `linux/arm64` - ARM 64-bit (Raspberry Pi 3/4/5 with 64-bit OS)
- `linux/arm/v7` - ARM 32-bit v7 (Raspberry Pi 2/3/4 with 32-bit OS)
- `linux/arm/v6` - ARM 32-bit v6 (Raspberry Pi Zero, Pi 1)
- `linux/386` - x86 32-bit

### Quick Setup

```bash
# 1. Copy and configure
cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml
# Edit config/xbee2mqtt.yaml with your settings

# 2. Update docker-compose.yml with your serial device
#    USB adapter: /dev/ttyUSB0 (default)
#    Raspberry Pi GPIO: /dev/ttyAMA0 or /dev/serial0

# 3. Start with Docker Compose
docker-compose up -d

# 4. View logs
docker-compose logs -f
```

**Raspberry Pi users:** If connecting XBee to GPIO UART pins, uncomment the Raspberry Pi device lines in `docker-compose.yml`. See [RASPBERRY_PI.md](docs/RASPBERRY_PI.md) for complete Raspberry Pi setup guide.

See [README.docker.md](docs/README.docker.md) for detailed Docker deployment instructions.

## Requirements

**Python 3.6 or higher** is required. All dependencies will be installed automatically.

### Option 1: Docker (Recommended)

- Docker and Docker Compose installed
- XBee coordinator radio connected via:
  - USB-to-Serial adapter (any Linux/macOS/Windows)
  - Raspberry Pi GPIO UART pins
  - Direct USB connection to Raspberry Pi

### Option 2: Native Installation

Install dependencies in a virtual environment:

```bash
# Create virtual environment and install dependencies
./do setup

# Or manually with pip
pip install -r requirements.txt
```

Required packages:
- pyyaml >= 5.4.1
- pyserial >= 3.5
- paho-mqtt >= 1.6.1
- parse >= 1.19.0
- xbee >= 2.3.2
- pytest >= 7.4.0 (for testing)

## Installation

### Docker Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd xbee2mqtt
   ```

2. Configure and run:
   ```bash
   cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml
   # Edit config/xbee2mqtt.yaml
   docker-compose up -d
   ```

### Native Installation

1. Clone the repository
2. Set up virtual environment:
   ```bash
   ./do setup
   ```

3. Configure the application (see Configuration section below)


## Configuration

Copy the sample configuration and edit it:

```bash
cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml
```

Then edit `config/xbee2mqtt.yaml` with your settings. The configuration is straightforward:


### general

**duplicate_check_window** lets you define a time window in seconds where messages for the same topic and with the same value will be ignored as duplicates.
**default_topic_pattern** lets you define a default topic for every message. It accepts two placeholders: {address} for the radio address and {port}. 
The port can be the radio pin (dio-12, adc-1, adc-7,...) or a string for messages sent through the UART of the sending radio.
**routes** dictionary defines the topics map. 
Set **publish_undefined_topic** False to filter out topics not defined in the routes dictionary. 
If it's True and the route is not defined it will be mapped to a topic defined by the **default_topic_pattern**.
For every defined route a subscription to the same route plus "/set" will be done. 
If the route maps to a digital port in the remote radio you can change its status to OUTPUT LOW ot OUTPUT HIGH by publishing a 0 or a 1 to this topic.


### radio

Configuration of the port where the XBee is attached to.
All messages are defined by the originating radio address (an 8 byte value) and a port or pin.
The **default_port_name** parameter lets you define what port name to use when the message was originally sent through the UART interface of the originating radio 
To send a custom message just send "port:value\n" through the UART interface of the radio, if no port is specified the **default_port_name** value will be used.


### mqtt

These are standard Mosquitto parameters. The status topic is the topic to post messages when the daemon starts or stops.


### processor

The processor is responsible for pre-processing the values before publishing them. There are several filters defined in libs/Filters.py


## Running

### With Docker

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart
```

### Native Deployment

The utility runs as a daemon. Control it with:

```bash
# Using the helper script (automatically uses virtualenv)
./do start
./do stop
./do restart

# Or directly with Python
python xbee2mqtt.py start
python xbee2mqtt.py stop
python xbee2mqtt.py restart
python xbee2mqtt.py reload  # Reload config without restarting
```

### Debugging

Monitor raw XBee messages:

```bash
./do console  # or: python xbee2console.py
```

## Testing

Verify the Python 3 migration and run tests:

```bash
# Verify migration (checks Python version, dependencies, syntax, imports)
python verify_migration.py

# Run unit tests
pytest tests/TestProcessor.py -v
# or: ./do tests
```

All tests should pass:
```
✅ Python version: 3.6+
✅ All dependencies installed
✅ No syntax errors
✅ All modules import successfully
✅ 10/10 filter tests passing
```

For detailed testing procedures, see the verification script output.

## Migration from Python 2

This project has been migrated from Python 2.7 to Python 3.9+. Key changes:

- ✅ Python 3.6+ required
- ✅ Modern test framework (pytest instead of nose)
- ✅ Updated dependencies (pyyaml instead of pyaml)
- ✅ Docker support with Python 3.9 base image
- ✅ All tests passing

If you were using an older version, simply:
1. Update your Python version to 3.6+
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Verify: `python verify_migration.py`

## Documentation

- **[README.docker.md](docs/README.docker.md)** - Docker deployment guide
- **[RASPBERRY_PI.md](docs/RASPBERRY_PI.md)** - Raspberry Pi setup guide (GPIO UART & USB)
- **[TESTING.md](docs/TESTING.md)** - Comprehensive testing guide
- **[requirements.txt](requirements.txt)** - Python dependencies

Browse all documentation in the [docs/](docs/) folder.

## License

GPL v3 - See [COPYING](COPYING) for details

## Support

For issues, questions, or contributions, please open an issue on the repository.




