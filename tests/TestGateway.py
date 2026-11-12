#! /usr/bin/python
# -*- coding: utf-8 -*-

import json
import unittest

from xbee2mqtt import Xbee2MQTT
from libs.ha_discovery import HADiscovery


class FakeMQTT(object):
    def __init__(self):
        self.published = []

    def publish(self, topic, value, qos=None, retain=None):
        self.published.append((topic, value, retain))

    def subscribe(self, topics):
        pass

    def unsubscribe(self, topics):
        pass


class FakeXBee(object):
    def __init__(self):
        self.queried = []

    def send_query(self, address, ports=None):
        self.queried.append(address)


class FakeProcessor(object):
    def process(self, topic, value):
        return value


class TestGateway(unittest.TestCase):

    def setUp(self):
        # Skip Daemon.__init__ (pidfile handling); wire collaborators by hand
        self.gw = Xbee2MQTT.__new__(Xbee2MQTT)
        self.gw.mqtt = FakeMQTT()
        self.gw.xbee = FakeXBee()
        self.gw.processor = FakeProcessor()
        self.gw.default_topic_pattern = '/raw/xbee/{address}/{port}'
        self.gw.expose_undefined_topics = False
        self.gw._topics = {}
        self.gw._discovered_entities = {}
        self.gw._device_pin_configs = {}
        self.gw._device_aliases = {}
        self.gw.ha_discovery = HADiscovery()
        self.gw.ha_discovery_enabled = True

    def topics(self):
        return [t for t, _, _ in self.gw.mqtt.published]

    def test_routes_match_uppercase_config_address(self):
        self.gw.load({'0013A2004097668A': {'seen': '/home/node/seen', 'alias': '/home/node/alias'}})
        self.assertEqual('/home/node/seen', self.gw._routes[('0013a2004097668a', 'seen')])
        self.assertEqual(('0013a2004097668a', 'seen'), self.gw._actions['/home/node/seen/set'])

    def test_identification_publishes_ha_discovery(self):
        self.gw.load({'0013a2004097668a': {'seen': '/home/node/seen', 'alias': '/home/node/alias'}})
        self.gw.xbee_on_identification('0013a2004097668a', 'XBEE_A')

        disc = 'homeassistant/sensor/xbee_0013a2004097668a/alias/config'
        self.assertIn(disc, self.topics())
        self.assertIn('/home/node/alias', self.topics())
        # Discovery config must be published before the state it describes
        self.assertLess(self.topics().index(disc), self.topics().index('/home/node/alias'))

        _, payload, retain = self.gw.mqtt.published[self.topics().index(disc)]
        config = json.loads(payload)
        self.assertTrue(retain)
        self.assertEqual('/home/node/alias', config['state_topic'])
        self.assertEqual(['xbee_0013a2004097668a'], config['device']['identifiers'])
        self.assertEqual(['0013a2004097668a'], self.gw.xbee.queried)

    def test_switch_discovery_has_command_topic(self):
        self.gw.load({'0013a2004097668a': {'dio-4': '/home/node/relay'}})
        self.gw._device_pin_configs[('0013a2004097668a', 'pin-4')] = 5
        self.gw.xbee_on_message('0013a2004097668a', 'dio-4', 1)

        disc = 'homeassistant/switch/xbee_0013a2004097668a/dio_4/config'
        self.assertIn(disc, self.topics())
        config = json.loads(self.gw.mqtt.published[self.topics().index(disc)][1])
        self.assertEqual('/home/node/relay/set', config['command_topic'])

    def test_unrouted_port_publishes_nothing(self):
        self.gw.load({})
        self.gw.xbee_on_identification('0013a2004097668a', 'XBEE_A')
        self.assertEqual([], self.gw.mqtt.published)


if __name__ == '__main__':
    unittest.main()
