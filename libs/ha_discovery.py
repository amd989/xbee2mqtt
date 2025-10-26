#! /usr/bin/python
# -*- coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

#   Xbee to MQTT gateway - Home Assistant MQTT Discovery
#   Copyright (C) 2025
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Alejandro Mora"
__contact__ = "mail@alejandro.md"
__copyright__ = "Copyright (C) 2025"
__license__ = 'GPL v3'

import json
import re
import logging


class HADiscovery(object):
    """
    Home Assistant MQTT Discovery payload generator for XBee devices.

    This class generates MQTT discovery configuration payloads that allow
    Home Assistant to automatically discover and configure XBee device entities
    (sensors, binary sensors, and switches) based on their port configurations.

    See: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
    """

    discovery_prefix = "homeassistant"
    node_name_pattern = "XBee {alias}"
    logger = None

    def __init__(self, discovery_prefix="homeassistant", node_name_pattern="XBee {alias}"):
        """
        Initialize the HADiscovery instance.

        Args:
            discovery_prefix: MQTT topic prefix for HA discovery (default: "homeassistant")
            node_name_pattern: Template for device names, supports {address} and {alias}
                              (default: "XBee {alias}")
        """
        self.discovery_prefix = discovery_prefix
        self.node_name_pattern = node_name_pattern

    def log(self, level, message):
        """
        Log a message if logger is configured.

        Args:
            level: Logging level (e.g., logging.INFO, logging.DEBUG)
            message: Message to log
        """
        if self.logger:
            self.logger.log(level, message)

    def _sanitize_port(self, port):
        """
        Convert port names to topic/ID-safe format.

        Replaces hyphens with underscores to ensure compatibility with
        MQTT topic naming conventions and Home Assistant entity IDs.

        Args:
            port: Port name (e.g., "dio-12", "adc-7")

        Returns:
            Sanitized port name (e.g., "dio_12", "adc_7")
        """
        return port.replace('-', '_')

    def generate_device_info(self, address, alias):
        """
        Generate the device information block for Home Assistant discovery.

        This creates a common device definition that groups all entities
        from the same XBee radio under a single device in Home Assistant.

        Args:
            address: XBee 64-bit address (e.g., "0013a200406bfd09")
            alias: Human-readable node name/alias

        Returns:
            Dictionary containing device information with structure:
            {
                "identifiers": ["xbee_<address>"],
                "name": "<formatted node name>",
                "manufacturer": "Digi",
                "model": "XBee ZigBee",
                "via_device": "xbee2mqtt"
            }
        """
        device_name = self.node_name_pattern.format(
            address=address,
            alias=alias if alias else address
        )

        return {
            "identifiers": [f"xbee_{address}"],
            "name": device_name,
            "manufacturer": "Digi",
            "model": "XBee ZigBee",
            "via_device": "xbee2mqtt"
        }

    def get_component_type(self, port, pin_value=None):
        """
        Determine the Home Assistant component type based on port and configuration.

        Maps XBee port types to appropriate Home Assistant entity types:
        - adc-N: sensor (analog input)
        - dio-N with pin_value=3: binary_sensor (digital input)
        - dio-N with pin_value=4 or 5: switch (digital output)
        - dio-N without pin_value: sensor (unknown configuration)
        - pin-N: sensor (configuration value)
        - seen: sensor (timestamp)
        - alias: sensor (text)

        Args:
            port: Port identifier (e.g., "dio-12", "adc-7", "seen")
            pin_value: Optional pin configuration value (3=input, 4=output low, 5=output high)

        Returns:
            Home Assistant component type: "sensor", "binary_sensor", or "switch"
        """
        if port.startswith('adc-'):
            return 'sensor'
        elif port.startswith('dio-'):
            if pin_value == 3:
                return 'binary_sensor'
            elif pin_value in [4, 5]:
                return 'switch'
            else:
                # Unknown configuration, default to sensor
                return 'sensor'
        elif port.startswith('pin-'):
            return 'sensor'
        elif port in ['seen', 'alias']:
            return 'sensor'
        else:
            return 'sensor'

    def get_discovery_topic(self, component, address, port):
        """
        Generate the MQTT discovery topic for a given entity.

        Home Assistant discovery topics follow this pattern:
        <discovery_prefix>/<component>/xbee_<address>/<port_safe>/config

        Args:
            component: HA component type ("sensor", "binary_sensor", or "switch")
            address: XBee 64-bit address
            port: Port identifier

        Returns:
            Complete MQTT discovery topic string
        """
        port_safe = self._sanitize_port(port)
        return f"{self.discovery_prefix}/{component}/xbee_{address}/{port_safe}/config"

    def generate_binary_sensor_config(self, address, alias, port, state_topic, name=None):
        """
        Generate Home Assistant binary sensor discovery configuration.

        Used for digital inputs (dio-N ports configured as inputs).
        Binary sensors represent ON/OFF states.

        Args:
            address: XBee 64-bit address
            alias: Human-readable node name
            port: Port identifier (e.g., "dio-12")
            state_topic: MQTT topic where state is published
            name: Optional friendly name (defaults to port name)

        Returns:
            Dictionary containing complete binary sensor configuration payload
        """
        port_safe = self._sanitize_port(port)
        unique_id = f"xbee_{address}_{port_safe}"

        if name is None:
            name = f"{alias or address} {port}"

        config = {
            "name": name,
            "unique_id": unique_id,
            "state_topic": state_topic,
            "payload_on": "1",
            "payload_off": "0",
            "device": self.generate_device_info(address, alias)
        }

        self.log(logging.DEBUG, f"Generated binary_sensor config for {unique_id}")
        return config

    def generate_switch_config(self, address, alias, port, state_topic, command_topic, name=None):
        """
        Generate Home Assistant switch discovery configuration.

        Used for digital outputs (dio-N ports configured as outputs).
        Switches can be controlled via MQTT commands.

        Args:
            address: XBee 64-bit address
            alias: Human-readable node name
            port: Port identifier (e.g., "dio-12")
            state_topic: MQTT topic where current state is published
            command_topic: MQTT topic to send commands (typically state_topic + "/set")
            name: Optional friendly name (defaults to port name)

        Returns:
            Dictionary containing complete switch configuration payload
        """
        port_safe = self._sanitize_port(port)
        unique_id = f"xbee_{address}_{port_safe}"

        if name is None:
            name = f"{alias or address} {port}"

        config = {
            "name": name,
            "unique_id": unique_id,
            "state_topic": state_topic,
            "command_topic": command_topic,
            "payload_on": "1",
            "payload_off": "0",
            "device": self.generate_device_info(address, alias)
        }

        self.log(logging.DEBUG, f"Generated switch config for {unique_id}")
        return config

    def generate_sensor_config(self, address, alias, port, state_topic, name=None,
                              device_class=None, unit_of_measurement=None):
        """
        Generate Home Assistant sensor discovery configuration.

        Used for analog inputs (adc-N), timestamps (seen), text values (alias),
        and pin configuration values (pin-N).

        Args:
            address: XBee 64-bit address
            alias: Human-readable node name
            port: Port identifier (e.g., "adc-7", "seen", "alias")
            state_topic: MQTT topic where sensor value is published
            name: Optional friendly name (defaults based on port type)
            device_class: Optional HA device class ("voltage", "timestamp", etc.)
            unit_of_measurement: Optional unit string (e.g., "mV", "°C")

        Returns:
            Dictionary containing complete sensor configuration payload
        """
        port_safe = self._sanitize_port(port)
        unique_id = f"xbee_{address}_{port_safe}"

        # Set default name based on port type if not provided
        if name is None:
            if port.startswith('adc-'):
                name = f"{alias or address} ADC {port[4:]}"
            elif port.startswith('pin-'):
                name = f"{alias or address} Pin {port[4:]} Config"
            elif port == 'seen':
                name = f"{alias or address} Last Seen"
            elif port == 'alias':
                name = f"{alias or address} Alias"
            else:
                name = f"{alias or address} {port}"

        config = {
            "name": name,
            "unique_id": unique_id,
            "state_topic": state_topic,
            "device": self.generate_device_info(address, alias)
        }

        # Add optional fields if provided
        if device_class:
            config["device_class"] = device_class

        if unit_of_measurement:
            config["unit_of_measurement"] = unit_of_measurement

        # Set defaults for specific port types
        if port.startswith('adc-'):
            if not device_class:
                config["device_class"] = "voltage"
            if not unit_of_measurement:
                config["unit_of_measurement"] = "mV"
        elif port == 'seen':
            if not device_class:
                config["device_class"] = "timestamp"

        self.log(logging.DEBUG, f"Generated sensor config for {unique_id}")
        return config


if __name__ == '__main__':
    # Example usage and testing
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    ha = HADiscovery()
    ha.logger = logger

    # Test device info generation
    print("\n=== Device Info ===")
    device_info = ha.generate_device_info("0013a200406bfd09", "Kitchen Sensor")
    print(json.dumps(device_info, indent=2))

    # Test component type detection
    print("\n=== Component Type Detection ===")
    print(f"adc-7: {ha.get_component_type('adc-7')}")
    print(f"dio-12 (pin_value=3): {ha.get_component_type('dio-12', pin_value=3)}")
    print(f"dio-12 (pin_value=5): {ha.get_component_type('dio-12', pin_value=5)}")
    print(f"pin-0: {ha.get_component_type('pin-0')}")
    print(f"seen: {ha.get_component_type('seen')}")

    # Test discovery topic generation
    print("\n=== Discovery Topics ===")
    print(ha.get_discovery_topic('sensor', '0013a200406bfd09', 'adc-7'))
    print(ha.get_discovery_topic('binary_sensor', '0013a200406bfd09', 'dio-12'))
    print(ha.get_discovery_topic('switch', '0013a200406bfd09', 'dio-11'))

    # Test configuration payloads
    print("\n=== Binary Sensor Config ===")
    binary_sensor = ha.generate_binary_sensor_config(
        "0013a200406bfd09",
        "Kitchen Sensor",
        "dio-12",
        "/home/kitchen/xbee/dio-12"
    )
    print(json.dumps(binary_sensor, indent=2))

    print("\n=== Switch Config ===")
    switch = ha.generate_switch_config(
        "0013a200406bfd09",
        "Kitchen Sensor",
        "dio-11",
        "/home/kitchen/xbee/dio-11",
        "/home/kitchen/xbee/dio-11/set"
    )
    print(json.dumps(switch, indent=2))

    print("\n=== Sensor Config (ADC) ===")
    adc_sensor = ha.generate_sensor_config(
        "0013a200406bfd09",
        "Kitchen Sensor",
        "adc-7",
        "/home/kitchen/xbee/adc-7"
    )
    print(json.dumps(adc_sensor, indent=2))

    print("\n=== Sensor Config (Timestamp) ===")
    seen_sensor = ha.generate_sensor_config(
        "0013a200406bfd09",
        "Kitchen Sensor",
        "seen",
        "/home/kitchen/xbee/seen"
    )
    print(json.dumps(seen_sensor, indent=2))

    print("\n=== Sensor Config (Pin Config) ===")
    pin_sensor = ha.generate_sensor_config(
        "0013a200406bfd09",
        "Kitchen Sensor",
        "pin-12",
        "/home/kitchen/xbee/pin-12"
    )
    print(json.dumps(pin_sensor, indent=2))
