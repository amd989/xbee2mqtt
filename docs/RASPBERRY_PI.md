# Raspberry Pi Setup Guide

This guide covers running xbee2mqtt on Raspberry Pi with XBee connected via GPIO UART or USB.

## Connection Options

### Option 1: USB Connection (Easiest)

Connect XBee to Raspberry Pi via USB-to-Serial adapter:
- **Device**: `/dev/ttyUSB0`
- **Advantages**: Plug and play, no configuration needed
- **Setup**: Use default `docker-compose.yml` settings

```bash
# Verify device
ls -l /dev/ttyUSB0

# Use default docker-compose.yml
docker-compose up -d
```

### Option 2: GPIO UART Connection

Connect XBee directly to Raspberry Pi GPIO pins:

**Pin connections:**
- XBee TX → GPIO 15 (Pin 10) - RX
- XBee RX → GPIO 14 (Pin 8) - TX
- XBee VCC → 3.3V (Pin 1)
- XBee GND → GND (Pin 6)

**Device**: `/dev/ttyAMA0` or `/dev/serial0`

## GPIO UART Setup

### 1. Enable UART

Edit `/boot/config.txt`:
```bash
sudo nano /boot/config.txt
```

Add or uncomment:
```
enable_uart=1
```

### 2. Disable Serial Console

Edit `/boot/cmdline.txt`:
```bash
sudo nano /boot/cmdline.txt
```

Remove these parameters if present:
```
console=serial0,115200
console=ttyAMA0,115200
```

### 3. Reboot

```bash
sudo reboot
```

### 4. Verify UART

After reboot, check the device:
```bash
# Check symlink
ls -l /dev/serial0

# Should show something like:
# /dev/serial0 -> ttyAMA0

# Test device exists
ls -l /dev/ttyAMA0
```

### 5. Set Permissions

```bash
# Option 1: Add user to dialout group (recommended)
sudo usermod -aG dialout $USER
# Then logout and login again

# Option 2: Change device permissions (temporary, resets on reboot)
sudo chmod 666 /dev/ttyAMA0
```

## Docker Configuration

### Update docker-compose.yml

Edit `docker-compose.yml` and uncomment the Raspberry Pi device lines:

```yaml
devices:
  # For USB adapter (default)
  # - /dev/ttyUSB0:/dev/ttyUSB0

  # For GPIO UART - uncomment one of these:
  - /dev/ttyAMA0:/dev/ttyAMA0
  # or use the symlink:
  # - /dev/serial0:/dev/serial0
```

### Update config/xbee2mqtt.yaml

Make sure the serial port matches:

```yaml
radio:
  port: /dev/ttyAMA0  # or /dev/serial0 for GPIO UART
  baudrate: 9600       # Match your XBee baudrate
```

## Running on Raspberry Pi

```bash
# 1. Configure
cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml
nano config/xbee2mqtt.yaml  # Edit with your settings

# 2. Update docker-compose.yml with correct device
nano docker-compose.yml

# 3. Start
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# Should see:
# "Connecting to Xbee"
# "Connected to MQTT broker"
```

## Raspberry Pi Models

### Raspberry Pi 3/4/5
- Primary UART: `/dev/ttyAMA0` (GPIO 14/15)
- Symlink: `/dev/serial0` → `/dev/ttyAMA0`
- Bluetooth UART: `/dev/ttyS0` (mini UART, avoid for XBee)

**Tip**: Use `/dev/serial0` symlink for portability across Pi models.

### Raspberry Pi Zero/1/2
- Primary UART: `/dev/ttyAMA0`
- No Bluetooth conflict
- Use `/dev/ttyAMA0` or `/dev/serial0`

## Troubleshooting

### "Permission denied" on /dev/ttyAMA0

```bash
# Check current permissions
ls -l /dev/ttyAMA0

# Add user to dialout group
sudo usermod -aG dialout $USER

# Logout and login again, or:
newgrp dialout

# Or temporarily change permissions
sudo chmod 666 /dev/ttyAMA0
```

### "Device not found"

```bash
# Check if UART is enabled
grep "enable_uart=1" /boot/config.txt

# Check for serial console (should NOT be there)
grep "console=serial0" /boot/cmdline.txt

# Verify device exists
ls -l /dev/ttyAMA* /dev/serial*

# Check kernel messages
dmesg | grep tty
```

### "Container starts but no XBee connection"

```bash
# Check config file has correct port
grep "port:" config/xbee2mqtt.yaml

# Check device is mapped in docker-compose.yml
docker-compose config | grep devices -A 2

# Test serial port manually (before starting container)
sudo apt-get install minicom
sudo minicom -D /dev/ttyAMA0 -b 9600
# Press Ctrl+A then Q to exit
```

### XBee not responding

1. **Check baudrate**: XBee and config must match (default: 9600)
2. **Check API mode**: XBee must be in API mode, not transparent mode
3. **Check wiring**: Ensure TX/RX are not swapped
4. **Check voltage**: XBee requires 3.3V (NOT 5V!)

## Performance Tips

### 1. Use ARM-optimized Docker Image

The Dockerfile automatically builds for ARM architecture on Raspberry Pi.

### 2. Reduce Docker Overhead

For better performance on older Pi models:
```yaml
# In docker-compose.yml
services:
  xbee2mqtt:
    # ... other settings ...
    mem_limit: 128m
    cpus: 0.5
```

### 3. Use Native Installation

For maximum performance on Raspberry Pi Zero/1:
```bash
# Install dependencies
sudo apt-get install python3 python3-pip python3-venv
./do setup

# Run natively (no Docker)
./do start
```

## Example: Complete Raspberry Pi Setup

```bash
# 1. Enable UART
echo "enable_uart=1" | sudo tee -a /boot/config.txt
sudo nano /boot/cmdline.txt  # Remove console=serial0,115200
sudo reboot

# 2. Clone repo
git clone <repo-url>
cd xbee2mqtt

# 3. Configure
cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml
nano config/xbee2mqtt.yaml  # Set port: /dev/ttyAMA0

# 4. Update Docker config
nano docker-compose.yml  # Uncomment /dev/ttyAMA0 line

# 5. Set permissions
sudo usermod -aG dialout $USER
newgrp dialout

# 6. Start
docker-compose up -d

# 7. Verify
docker-compose logs -f
```

## Additional Resources

- [Raspberry Pi UART Documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts)
- [XBee Configuration Guide](https://www.digi.com/resources/documentation/digidocs/90001456-13/)
- [Docker on Raspberry Pi](https://docs.docker.com/engine/install/debian/)

## Common Configurations

### Home Automation Hub
```yaml
# config/xbee2mqtt.yaml
mqtt:
  host: localhost  # Run Mosquitto on same Pi
  port: 1883

radio:
  port: /dev/ttyAMA0
  baudrate: 9600

general:
  discovery_on_connect: True  # Auto-discover XBee nodes
```

### Remote Gateway
```yaml
# config/xbee2mqtt.yaml
mqtt:
  host: 192.168.1.100  # Remote MQTT broker
  username: iot_user
  password: secure_password

radio:
  port: /dev/ttyUSB0  # USB adapter for flexibility
```

## Monitoring

Monitor CPU and memory usage:
```bash
# Container stats
docker stats xbee2mqtt

# System stats
vcgencmd measure_temp  # CPU temperature
free -h                # Memory usage
```

Ideal for Raspberry Pi 3/4/5. For Raspberry Pi Zero/1/2, consider native installation for better performance.
