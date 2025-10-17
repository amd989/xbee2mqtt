#! /usr/bin/python
# -*- coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

#   Copyright (C) 2013 by Xose Pérez
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

__author__ = "Xose Pérez"
__contact__ = "xose.perez@gmail.com"
__copyright__ = "Copyright (C) 2013 Xose Pérez"
__license__ = 'GPL v3'

from paho.mqtt.client import Client as Mosquitto, MQTTv311
try:
    from paho.mqtt.client import CallbackAPIVersion
    PAHO_V2 = True
except ImportError:
    PAHO_V2 = False
import ctypes
import time
import logging

# Class messages
MSG_CONNECTED = 1
MSG_DISCONNECTED = 2

class MosquittoWrapper(Mosquitto):
    """
    Wrapper for the official Mosquitto client that allows injection and easy mocking
    """

    host = 'localhost'
    port = 1883
    username = None
    password = None

    keepalive = 60
    qos = 0
    retain = False
    set_will = True

    status_topic = '/service/%s/status'
    subscribe_to = []

    connected = False
    logger = None

    on_message_cleaned = None

    _subscriptions = {}

    def __init__(self, client_id="", clean_session=None, userdata=None, protocol=None, transport="tcp"):
        """
        Initialize with compatibility for both paho-mqtt v1.x and v2.x
        """
        # Default to MQTTv311 if protocol not specified
        if protocol is None:
            protocol = MQTTv311

        if PAHO_V2:
            # paho-mqtt v2.x requires CallbackAPIVersion and uses different parameter names
            # Note: clean_session doesn't exist in v2.x, it's handled by MQTTv5/v3.1.1 protocol automatically
            init_params = {
                'callback_api_version': CallbackAPIVersion.VERSION1,
                'client_id': client_id,
                'userdata': userdata,
                'protocol': protocol,
                'transport': transport
            }
            # Only pass clean_session if explicitly set (v2.x defaults handle this)
            # In v2.x with VERSION1 callbacks, clean_session is still supported
            if clean_session is not None:
                init_params['clean_session'] = clean_session
            super(MosquittoWrapper, self).__init__(**init_params)
        else:
            # paho-mqtt v1.x
            super(MosquittoWrapper, self).__init__(
                client_id=client_id,
                clean_session=clean_session,
                userdata=userdata,
                protocol=protocol,
                transport=transport
            )

    def log(self, level, message):
        if self.logger:
            self.logger.log(level, message)

    def connect(self):
        """
        Connects to the Mosquitto broker with the pre-configured parameters
        """
        self.on_connect = self.__on_connect
        self.on_message = self.__on_message
        self.on_disconnect = self.__on_disconnect
        self.on_subscribe = self.__on_subscribe
        self.on_unsubscribe = self.__on_unsubscribe
        self.on_log = self.__on_log
        if self.username:
            self.username_pw_set(self.username, self.password)
        if self.set_will:
            # Decode client_id from bytes to string for Python 3 compatibility
            client_id_str = self._client_id.decode('utf-8') if isinstance(self._client_id, bytes) else self._client_id
            self.will_set(self.status_topic % client_id_str, "0", self.qos, self.retain)
        self.log(logging.INFO, "Connecting to MQTT broker at %s:%s" % (self.host, self.port))
        # Ensure host is a valid string (paho-mqtt v2.x is strict about validation)
        if not self.host or not isinstance(self.host, str):
            raise ValueError("MQTT host must be a valid string, got: %s" % repr(self.host))
        Mosquitto.connect(self, self.host, self.port, self.keepalive)

    def subscribe(self, topics):
        """
        Subscribe to a given topic
        """
        if not isinstance(topics, list):
            topics = [topics]
        for topic in topics:
            rc, mid = Mosquitto.subscribe(self, topic, 0)
            self._subscriptions[mid] = topic
            self.log(logging.INFO, "Sent subscription request to topic %s" % topic)

    def unsubscribe(self, topics):
        """
        Unsubscribe of a given topic
        """
        if not isinstance(topics, list):
            topics = [topics]
        for topic in topics:
            rc, mid = Mosquitto.unsubscribe(self, topic)
            self._subscriptions[mid] = topic
            self.log(logging.INFO, "Sent unsubscription request of topic %s" % topic)

    def publish(self, topic, value, qos=None, retain=None):
        """
        Publishes a value to a given topic, uses pre-loaded values for QoS and retain
        """
        qos = qos if qos is not None else self.qos
        retain = retain if retain is not None else self.retain
        # Ensure topic is a string for Python 3 compatibility
        if isinstance(topic, bytes):
            topic = topic.decode('utf-8')
        Mosquitto.publish(self, topic, str(value), qos, retain)

    def __on_connect(self, mosq, obj, flags, rc):
        """
        Callback when connection to the MQTT broker has succedeed or failed
        """
        if rc == 0:
            self.log(logging.INFO , "Connected to MQTT broker")
            # Decode client_id from bytes to string for Python 3 compatibility
            client_id_str = self._client_id.decode('utf-8') if isinstance(self._client_id, bytes) else self._client_id
            self.publish(self.status_topic % client_id_str, "1")
            self.subscribe(self.subscribe_to)
            self.connected = True
        else:
            self.log(logging.ERROR , "Could not connect to MQTT broker")
            self.connected = False

    def __on_disconnect(self, mosq, obj, rc):
        """
        Callback when disconnecting from the MQTT broker
        """
        self.connected = False
        self.log(logging.INFO, "Disconnected from MQTT broker")
        if rc != 0:
            time.sleep(3)
            self.connect()

    def __on_message(self, mosq, obj, msg):
        """
        Incoming message
        """
        if self.on_message_cleaned:
            try:
                message = ctypes.string_at(msg.payload, msg.payloadlen)
            except:
                message = msg.payload
            self.on_message_cleaned(msg.topic, message)

    def __on_subscribe(self, mosq, obj, mid, qos_list):
        """
        Callback when succeeded subscription
        """
        topic = self._subscriptions.get(mid, 'Unknown')
        self.log(logging.INFO, "Subscription to topic %s confirmed" % topic)

    def __on_unsubscribe(self, mosq, obj, mid):
        """
        Callback when succeeded an unsubscription
        """
        topic = self._subscriptions.get(mid, 'Unknown')
        self.log(logging.INFO, "Unsubscription of topic %s confirmed" % topic)

    def __on_log(self, mosq, obj, level, string):
        self.log(logging.DEBUG, string)


if __name__ == '__main__':

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    mqtt = MosquittoWrapper('mosquitto_test_client_2')
    mqtt.subscribe_to = ['/test']
    mqtt.logger = logger
    mqtt.connect()

    rc = 0
    while rc == 0:
        rc = mqtt.loop()
    print("rc: "+str(rc))

