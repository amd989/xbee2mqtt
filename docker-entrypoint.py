#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Docker entrypoint that runs xbee2mqtt in foreground mode
"""

import os
import sys
import logging
from serial import Serial, SerialException

# Add app directory to path
sys.path.insert(0, '/app')

from parse import parse
from libs.daemon import Daemon
from libs.processor import Processor
from libs.config import Config
from libs.mosquitto_wrapper import MosquittoWrapper
from libs.xbee_wrapper import XBeeWrapper
from xbee2mqtt import Xbee2MQTT

def resolve_path(path):
    return path if path[0] == '/' else os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

if __name__ == "__main__":
    config_file = resolve_path('config/xbee2mqtt.yaml')
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
    mqtt.status_topic = config.get('mqtt', 'status_topic', '/service/%s/status')
    mqtt.set_will = config.get('mqtt', 'set_will', True)

    try:
        serial = Serial(
            config.get('radio', 'port', '/dev/ttyUSB0'),
            config.get('radio', 'baudrate', 9600)
        )
    except SerialException as e:
        logger.error("Could not open serial port: %s" % e)
        sys.exit(1)

    xbee = XBeeWrapper()
    xbee.serial = serial
    xbee.default_port_name = config.get('radio', 'default_port_name', 'serial')
    xbee.sample_rate = config.get('general', 'sample_rate', 0)
    xbee.change_detection = config.get('general', 'change_detection', False)

    processor = Processor(config.get('processor', 'filters', []))

    # Create instance but DON'T use it as a daemon
    # We just use its run() method directly in foreground
    xbee2mqtt = Xbee2MQTT('/tmp/fake.pid')  # Pidfile won't be used
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

    # Run in foreground - Docker handles process management
    logger.info("Starting xbee2mqtt in foreground mode for Docker")
    try:
        xbee2mqtt.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        xbee2mqtt.cleanup()
    except Exception as e:
        logger.exception("Fatal error: %s" % e)
        sys.exit(1)
