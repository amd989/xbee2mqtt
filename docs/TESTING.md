# Testing Guide for xbee2mqtt

This guide explains how to verify the Python 2 to Python 3 migration and test the application.

## Quick Verification

The fastest way to verify the migration:

```bash
# Run the automated verification script
python3 verify_migration.py
```

This will check:
- ✅ Python version compatibility
- ✅ Required dependencies
- ✅ Syntax validation
- ✅ Import checks
- ✅ Python 2 pattern detection

## Detailed Testing Steps

### Step 1: Environment Setup

**Option A: Native Python (for development)**

```bash
# Install dependencies
pip3 install -r requirements.txt

# Verify installation
python3 verify_migration.py
```

**Option B: Docker (for production testing)**

```bash
# Build Docker image
docker build -t xbee2mqtt .

# Verify image was created
docker images | grep xbee2mqtt
```

### Step 2: Syntax and Import Testing

Test that all Python files compile and import correctly:

```bash
# Compile all Python files
python3 -m py_compile xbee2mqtt.py
python3 -m py_compile libs/*.py

# Test imports
python3 -c "from libs.config import Config; print('✅ Config OK')"
python3 -c "from libs.processor import Processor; print('✅ Processor OK')"
python3 -c "from libs.filters import FilterFactory; print('✅ Filters OK')"
python3 -c "from libs.xbee_wrapper import XBeeWrapper; print('✅ XBee OK')"
python3 -c "from libs.mosquitto_wrapper import MosquittoWrapper; print('✅ MQTT OK')"
python3 -c "from libs.daemon import Daemon; print('✅ Daemon OK')"
```

### Step 3: Configuration Validation

Test that configuration parsing works:

```bash
# Create test config
cp config/xbee2mqtt.yaml.sample config/xbee2mqtt.yaml

# Test config loading
python3 -c "
from libs.config import Config
c = Config('config/xbee2mqtt.yaml')
print('✅ Config loaded')
print('MQTT Host:', c.get('mqtt', 'host'))
print('Radio Port:', c.get('radio', 'port'))
"
```

### Step 4: Filter Testing

Run the built-in filter tests:

```bash
# Run filter processor tests
pytest tests/TestProcessor.py -v

# Run XBee wrapper tests
pytest tests/TestXBee.py -v

# Run all tests
pytest tests/ -v
```

Expected output:
```
collected X items

tests/TestProcessor.py::TestProcessor::test_boolean_filter PASSED
tests/TestProcessor.py::TestProcessor::test_enum_filter PASSED
tests/TestProcessor.py::TestProcessor::test_linear_filter PASSED
tests/TestProcessor.py::TestProcessor::test_not_filter PASSED
tests/TestProcessor.py::TestProcessor::test_round_filter PASSED
...

====== X passed in Y.YYs ======
```

### Step 5: Docker Container Testing

Test the Docker containerization:

```bash
# Build image
docker build -t xbee2mqtt .

# Test Python version in container
docker run --rm xbee2mqtt python3 --version

# Test dependencies in container
docker run --rm xbee2mqtt python3 -c "
import yaml
import serial
import paho.mqtt.client
import parse
import xbee
print('✅ All dependencies available')
"

# Test config loading in container
docker run --rm \
  -v $(pwd)/config:/app/config:ro \
  xbee2mqtt \
  python3 -c "from libs.config import Config; c = Config('/app/config/xbee2mqtt.yaml'); print('✅ Config OK')"
```

### Step 6: Integration Testing (With Hardware)

**Prerequisites:**
- XBee coordinator connected to USB port (e.g., `/dev/ttyUSB0`)
- MQTT broker running (e.g., Mosquitto)
- Valid configuration file

**Test procedure:**

```bash
# 1. Check XBee device is detected
ls -l /dev/ttyUSB*

# 2. Update config with correct serial port and MQTT broker
nano config/xbee2mqtt.yaml

# 3. Start in foreground to see logs
docker-compose up

# Or with native Python:
python3 xbee2mqtt.py start
```

**Watch for these log messages:**

```
✅ "Starting Xbee to MQTT gateway v0.7.20160903"
✅ "Connecting to Xbee"
✅ "Connecting to MQTT broker"
✅ "Connected to MQTT broker"
✅ "Subscription to topic ... confirmed"
```

**If discovery is enabled:**
```
✅ "Requesting Node Discovery"
✅ "Identification received from radio: ..."
```

**Test XBee → MQTT:**
1. Trigger an event on a remote XBee node (button press, sensor reading, etc.)
2. Watch for log: `"Message received from radio: ..."`
3. Watch for log: `"Sending message to MQTT broker: ..."`
4. Use MQTT client to verify message was published:
   ```bash
   mosquitto_sub -h localhost -t '#' -v
   ```

**Test MQTT → XBee:**
1. Publish a command via MQTT:
   ```bash
   mosquitto_pub -h localhost -t '/test/dio10/set' -m '1'
   ```
2. Watch for log: `"Message received from MQTT broker: ..."`
3. Watch for log: `"Setting radio ... port ... to ..."`
4. Verify the XBee pin changed state

### Step 7: Long-Running Stability Test

Test for memory leaks or issues over time:

```bash
# Start in background
docker-compose up -d

# Monitor for 24 hours
watch -n 60 'docker stats xbee2mqtt --no-stream'

# Check logs periodically
docker-compose logs --tail=100

# Check for errors
docker-compose logs | grep -i error
docker-compose logs | grep -i exception
```

**Expected behavior:**
- Memory usage remains stable
- No Python exceptions in logs
- Container stays healthy

## Common Issues and Solutions

### Issue: "No module named 'yaml'"

**Solution:**
```bash
pip3 install pyyaml
# or
docker-compose build --no-cache
```

### Issue: "Permission denied: '/dev/ttyUSB0'"

**Solution:**
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Or adjust permissions
sudo chmod 666 /dev/ttyUSB0

# For Docker, ensure device is mapped correctly
docker-compose.yml:
  devices:
    - /dev/ttyUSB0:/dev/ttyUSB0
```

### Issue: "SyntaxError" or "NameError"

**Solution:**
Run the verification script to identify the issue:
```bash
python3 verify_migration.py
```

Check the specific file mentioned in the error.

### Issue: "KeyError" or "AttributeError"

**Possible causes:**
- Dictionary key access changed in Python 3
- Bytes vs. string handling differences

**Solution:**
Check the error traceback and compare with the original Python 2 code.

### Issue: MQTT messages not received

**Troubleshooting:**
```bash
# 1. Verify MQTT broker is accessible
mosquitto_pub -h localhost -t 'test' -m 'hello'
mosquitto_sub -h localhost -t 'test'

# 2. Check daemon subscriptions in logs
docker-compose logs | grep -i "subscription"

# 3. Verify topic patterns in config
cat config/xbee2mqtt.yaml | grep -A5 routes
```

### Issue: XBee messages not processed

**Troubleshooting:**
```bash
# 1. Verify XBee is in API mode (not transparent mode)
# Use XCTU software or check manually

# 2. Check baudrate matches XBee configuration
cat config/xbee2mqtt.yaml | grep baudrate

# 3. Test with console tool to see raw packets
./do console
# or
python3 xbee2console.py
```

## Automated Testing

For CI/CD pipelines:

```bash
#!/bin/bash
set -e

echo "Running Python 3 verification..."
python3 verify_migration.py || exit 1

echo "Running unit tests..."
pytest tests/ -v || exit 1

echo "Building Docker image..."
docker build -t xbee2mqtt . || exit 1

echo "Testing Docker container..."
docker run --rm xbee2mqtt python3 verify_migration.py || exit 1

echo "✅ All tests passed!"
```

## Performance Benchmarks

After migration, Python 3 should show:

- **Startup time**: ~2-3 seconds (similar to Python 2)
- **Memory usage**: ~50-80 MB (slightly higher than Python 2 due to Unicode strings)
- **Message throughput**: >100 messages/second (similar or better than Python 2)
- **CPU usage**: <5% idle, <20% under load (similar to Python 2)

Monitor with:
```bash
docker stats xbee2mqtt
```

## Reporting Issues

If you find migration issues:

1. Run `python3 verify_migration.py` and save output
2. Collect error logs: `docker-compose logs > error.log`
3. Note Python version: `python3 --version`
4. Note OS: `uname -a` or `systeminfo`
5. Describe expected vs. actual behavior
6. Include configuration (redact secrets)

## Success Criteria

The migration is successful when:

- ✅ All verification checks pass
- ✅ All unit tests pass
- ✅ Container builds without errors
- ✅ Daemon starts and connects to XBee
- ✅ Daemon connects to MQTT broker
- ✅ XBee messages are received and published to MQTT
- ✅ MQTT commands control XBee pins
- ✅ No Python errors in logs for 24+ hours
- ✅ Memory usage remains stable

Once all criteria are met, the migration is complete and production-ready!
