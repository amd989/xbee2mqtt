#! /usr/bin/python
# -*- coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

#   Xbee to MQTT gateway
#   Copyright (C) 2012-2013 by Xose Pérez
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

__app__ = "Xbee to MQTT gateway"
__version__ = "0.9.20251025"
__author__ = "Xose Pérez"
__contact__ = "xose.perez@gmail.com"
__copyright__ = "Copyright (C) 2012-2013 Xose Pérez"
__license__ = 'GPL v3'

import os
import re
import sys
import time
import logging

#from tests.SerialMock import Serial
from parse import parse
from serial import Serial
from serial import SerialException
from libs.daemon import Daemon
from libs.processor import Processor
from libs.config import Config
from libs.mosquitto_wrapper import MosquittoWrapper
from libs.xbee_wrapper import XBeeWrapper
from libs.ha_discovery import HADiscovery

class Xbee2MQTT(Daemon):
    """
    Xbee2MQTT daemon.
    Glues the different components together
    """

    duplicate_check_window = 5

    logger = None
    xbee = None
    mqtt = None
    processor = None
    config_file = None

    _routes = {}
    _actions = {}
    _topics = {}

    ha_discovery = None  # HADiscovery instance
    ha_discovery_enabled = False
    ha_discovery_prefix = "homeassistant"
    _discovered_entities = {}  # Track published entities: {(address, port): True}
    _device_pin_configs = {}  # Track pin configs: {(address, port): value}
    _device_aliases = {}  # Track device aliases: {address: alias}

    def load(self, routes):
        """
        Read configuration and store bidirectional dicts
        """
        self._routes = {}
        self._actions = {}
        for address, ports in routes.items():
            for port, topic in ports.items():
                self._routes[(address, port)] = topic
                self._actions['%s/set' % topic] = (address, port)

    def log(self, level, message):
        if self.logger:
            self.logger.log(level, message)

    def cleanup(self):
        """
        Clean up connections and unbind ports
        """
        self.xbee.disconnect()
        self.log(logging.INFO, "Exiting")
        self.mqtt.disconnect()
        sys.exit()

    def mqtt_on_message(self, topic, message):
        """
        Message received from a subscribed topic
        """

        self.log(logging.DEBUG, "Message received from MQTT broker: %s %s" % (topic, message))

        data = self._actions.get(topic, None)
        if data is None:
            result = parse(self.default_input_topic_pattern, topic).named

            new_schema = re.search('{item}', self.default_topic_pattern)
            if new_schema:
                number = result['port'][4:]
                item = result['item']

                if item == 'analog':
                    result['port'] = 'adc-%s' % number
                elif item == 'digital':
                    result['port'] = 'dio-%s' % number
                elif item == 'config':
                    result['port'] = 'pin-%s' % number

            data = (result['address'], result['port'])

        if data:
            address, port = data
            self.log(logging.INFO, "Setting radio %s port %s to %s" % (address, port, message))
            try:
                self.xbee.send_message(address, port, message)
            except Exception as e:
                self.log(logging.ERROR, "Error while sending message (%s)" % e)

    def mqtt_publish(self, topic, value):
        """
        Publishes a non duplicate value to a given topic
        """
        if topic:

            now = time.time()
            if topic in self._topics \
                and self._topics[topic]['time'] + self.duplicate_check_window > now \
                and self._topics[topic]['value'] == value \
                :
                    self.log(logging.DEBUG, "Duplicate removed")
                    return
            self._topics[topic] = {'time': now, 'value': value}

            value = self.processor.process(topic, value)
            self.log(logging.INFO, "Sending message to MQTT broker: %s %s" % (topic, value))
            self.mqtt.publish(topic, value)

    def transform_pattern(self, pattern, address, port):
        """
        Transform default topic pattern to expand adc/dio ports if there is a {item} whitin
        to keep compatibility with old topic patterns schemas.
        """
        prefix = port[:4]
        if prefix == 'adc-':
            item = 'analog'
        elif prefix == 'dio-':
            item = 'digital'
        elif prefix == 'pin-':
            item = 'config'
        else:
            item = ''

        new_schema = re.search('{item}', pattern)
        if new_schema:
            number = port[4:]
            port = "pin-%s" % number if len(item)>0 else port
            topic = pattern.format(address=address, port=port, item=item)
        else:
            topic = pattern.format(address=address, port=port)

        # Clean excess slashes.
        return re.sub('//+|/$', '', topic).rstrip('/')

    def xbee_on_message(self, address, port, value):
        """
        Message from the radio coordinator
        """
        self.log(logging.DEBUG, "Message received from radio: %s %s %s" % (address, port, value))

        topic = self._routes.get(
            (address, port),
            self.transform_pattern(self.default_topic_pattern, address, port) if self.expose_undefined_topics else False
        )
        prefix = port[:4]

        # Track pin configurations for HA discovery
        if prefix == 'pin-':
            self._device_pin_configs[(address, port)] = value
            # Also determine if corresponding dio should be discovered
            number = port[4:]
            dio_port = 'dio-%s' % number
            dio_pin_value = value  # 3 = input, 4/5 = output

        if self.expose_undefined_topics and prefix in ['dio-', 'pin-']:
            self.mqtt.subscribe(self.transform_pattern(self.default_input_topic_pattern, address, port))
            number = port[4:]
            digital = 'dio-%s' % number
            digital_topic = self.transform_pattern(self.default_input_topic_pattern, address, digital)
            if prefix == 'pin-' and value in [4, 5]:
                self.mqtt.subscribe(digital_topic)
            else:
                self.mqtt.unsubscribe(digital_topic)

        # Get alias if known, otherwise use address
        alias = self._device_aliases.get(address, None)

        # Get pin configuration if this is a dio port
        pin_value = None
        if prefix == 'dio-':
            number = port[4:]
            pin_port = 'pin-%s' % number
            pin_value = self._device_pin_configs.get((address, pin_port), None)

        # Publish HA discovery before publishing state
        self.publish_ha_discovery(address, alias, port, topic, pin_value)

        self.mqtt_publish(topic, value)

    def xbee_on_identification(self, address, alias):
        """
        Identification message from remote node
        """
        now = time.strftime("%s")
        self.log(logging.INFO, "Identification received from radio: %s (%s) %s" % (address, alias, now))

        # Store alias for future reference
        self._device_aliases[address] = alias

        topic_for_seen = self._routes.get(
            (address, "seen"),
            self.transform_pattern(self.default_topic_pattern, address, "seen") if self.expose_undefined_topics else False
        )

        topic_for_alias = self._routes.get(
            (address, "alias"),
            self.transform_pattern(self.default_topic_pattern, address, "alias") if self.expose_undefined_topics else False
        )

        # Publish HA discovery for seen and alias before publishing state
        self.publish_ha_discovery(address, alias, "seen", topic_for_seen)
        self.publish_ha_discovery(address, alias, "alias", topic_for_alias)

        self.mqtt_publish(topic_for_seen, now)
        self.mqtt_publish(topic_for_alias, alias)
        self.xbee.send_query(address)

    def publish_ha_discovery(self, address, alias, port, topic, pin_value=None):
        """
        Publish Home Assistant MQTT Discovery configuration for an entity
        """
        import json

        # Skip if HA discovery is disabled
        if not self.ha_discovery_enabled:
            return

        # Skip if already discovered
        entity_key = (address, port)
        if entity_key in self._discovered_entities:
            return

        # Determine component type
        component_type = self.ha_discovery.get_component_type(port, pin_value)
        if not component_type:
            return

        # Get or create device info
        device_name = alias if alias else address
        device_info = self.ha_discovery.get_device_info(address, device_name)

        # Generate entity config based on component type
        if component_type == 'sensor':
            config = self.ha_discovery.get_sensor_config(address, port, topic, device_info)
        elif component_type == 'binary_sensor':
            config = self.ha_discovery.get_binary_sensor_config(address, port, topic, device_info)
        elif component_type == 'switch':
            config = self.ha_discovery.get_switch_config(address, port, topic, device_info)
        else:
            return

        # Build discovery topic
        discovery_topic = self.ha_discovery.get_discovery_topic(component_type, address, port)

        # Publish discovery config with retain=True
        self.log(logging.INFO, "Publishing HA discovery for %s %s: %s" % (address, port, discovery_topic))
        self.mqtt.publish(discovery_topic, json.dumps(config), retain=True)

        # Mark as discovered
        self._discovered_entities[entity_key] = True

    def do_reload(self):
        self.log(logging.INFO, "Reloading")
        config = Config(config_file)
        self.load(config.get('general', 'routes', {}))
        self.mqtt.subscribe(list(self._actions.keys()))

    def run(self):
        """
        Entry point, initiates components and loops forever...
        """
        self.log(logging.INFO, "Starting " + __app__ + " v" + __version__)
        self.mqtt.on_message_cleaned = self.mqtt_on_message
        self.mqtt.subscribe_to = list(self._actions.keys())
        self.mqtt.logger = self.logger
        self.xbee.on_identification = self.xbee_on_identification
        self.xbee.on_node_discovery = self.xbee_on_identification
        self.xbee.on_message = self.xbee_on_message
        self.xbee.logger = self.logger

        self.mqtt.connect()
        if not self.xbee.connect():
            self.stop()

        if self.discovery_on_connect:
            self.log(logging.INFO, "Requesting Node Discovery")
            self.xbee.xbee.at(command='ND')

        while True:
            try:
                self.mqtt.loop()
            except Exception as e:
                logging.exception("Error while looping MQTT (%s)" % e)

if __name__ == "__main__":

    def resolve_path(path):
        return path if path[0] == '/' else os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

    config_file = resolve_path('config/xbee2mqtt.yaml');
    config = Config(config_file)

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(config.get('daemon', 'logging_level', logging.INFO))
    logger.addHandler(handler)

    mqtt = MosquittoWrapper(config.get('mqtt', 'client_id', None))
    mqtt.host = config.get('mqtt', 'host', 'localhost')
    mqtt.port = config.get('mqtt', 'port', 1883)
    mqtt.username = config.get('mqtt', 'username', None)
    mqtt.password = config.get('mqtt', 'password', None)
    mqtt.keepalive = config.get('mqtt', 'keepalive', 60)
    mqtt.clean_session = config.get('mqtt', 'clean_session', False)
    mqtt.qos = config.get('mqtt', 'qos', 0)
    mqtt.retain = config.get('mqtt', 'retain', True)
    mqtt.set_will = config.get('mqtt', 'set_will', True)

    try:
        serial = Serial(
            config.get('radio', 'port', '/dev/ttyUSB0'),
            config.get('radio', 'baudrate', 9600)
        )
    except SerialException as e:
        sys.exit(e)

    xbee = XBeeWrapper()
    xbee.serial = serial
    xbee.default_port_name = config.get('radio', 'default_port_name', 'serial')
    xbee.sample_rate = config.get('general', 'sample_rate', 0)
    xbee.change_detection = config.get('general', 'change_detection', False)

    processor = Processor(config.get('processor', 'filters', []))

    xbee2mqtt = Xbee2MQTT(resolve_path(config.get('daemon', 'pidfile', '/tmp/xbee2mqtt.pid')))
    xbee2mqtt.stdout = resolve_path(config.get('daemon', 'stdout', '/dev/null'))
    xbee2mqtt.stderr = resolve_path(config.get('daemon', 'stderr', xbee2mqtt.stdout))
    xbee2mqtt.discovery_on_connect = config.get('general', 'discovery_on_connect', True)
    xbee2mqtt.duplicate_check_window = config.get('general', 'duplicate_check_window', 5)
    xbee2mqtt.default_output_topic_pattern = config.get(
        'general', 'default_output_topic_pattern', '/raw/xbee/{address}/{port}'
    )
    xbee2mqtt.default_topic_pattern = config.get(
        'general', 'default_topic_pattern', xbee2mqtt.default_output_topic_pattern
    )
    xbee2mqtt.default_input_topic_pattern = config.get(
        'general', 'default_input_topic_pattern', xbee2mqtt.default_topic_pattern + '/set'
    )
    xbee2mqtt.publish_undefined_topics = config.get('general', 'publish_undefined_topics', True)
    xbee2mqtt.expose_undefined_topics = config.get(
        'general', 'expose_undefined_topics', xbee2mqtt.publish_undefined_topics
    )
    xbee2mqtt.load(config.get('general', 'routes', {}))
    xbee2mqtt.logger = logger
    xbee2mqtt.mqtt = mqtt
    xbee2mqtt.xbee = xbee
    xbee2mqtt.processor = processor
    xbee2mqtt.config_file = config_file

    # Initialize Home Assistant MQTT Discovery
    xbee2mqtt.ha_discovery_enabled = config.get('homeassistant', 'discovery', False)
    xbee2mqtt.ha_discovery_prefix = config.get('homeassistant', 'discovery_prefix', 'homeassistant')
    if xbee2mqtt.ha_discovery_enabled:
        xbee2mqtt.ha_discovery = HADiscovery(
            discovery_prefix=xbee2mqtt.ha_discovery_prefix,
            node_name_pattern=config.get('homeassistant', 'node_name_pattern', 'XBee {alias}')
        )
        logger.log(logging.INFO, "Home Assistant MQTT Discovery enabled")

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            xbee2mqtt.start()
        elif 'stop' == sys.argv[1]:
            xbee2mqtt.stop()
        elif 'restart' == sys.argv[1]:
            xbee2mqtt.restart()
        elif 'reload' == sys.argv[1]:
            xbee2mqtt.reload()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)

