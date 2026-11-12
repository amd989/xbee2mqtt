#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Xose Pérez"
__contact__ = "xose.perez@gmail.com"
__copyright__ = "Copyright (C) Xose Pérez"
__license__ = 'GPL v3'

import unittest
import time
import binascii

from .SerialMock import Serial
from libs.xbee_wrapper import XBeeWrapper

class TestXBee(unittest.TestCase):

    serial = None
    xbee = None
    messages = []

    def setUp(self):
        self.messages = []
        self.serial = Serial(None, None)
        self.xbee = XBeeWrapper()
        self.xbee.default_port_name = 'serial'
        self.xbee.serial = self.serial
        self.xbee.on_message = self.on_message
        self.xbee.connect()

    def tearDown(self):
        self.xbee.disconnect()

    def on_message(self, address, port, value):
        self.messages += [{
            'address': address,
            'port': port,
            'value': value
        }]

    def wait(self, condition=None, timeout=5):
        condition = condition or (lambda: len(self.messages) > 0)
        deadline = time.time() + timeout
        while not condition():
            if time.time() > deadline:
                self.fail("Timed out waiting for XBee frame to be processed")
            time.sleep(.1)
        time.sleep(.1)
    def test_x90_malformed(self):
        self.serial.feed('900013a20040401122012340' + binascii.hexlify('AABBCCDD\n'.encode()).decode()) # Receive mal-formed serial packet
        self.wait()
        self.assertEqual(1, len(self.messages))
        self.assertEqual('0013a20040401122', self.messages[0]['address'])
        self.assertEqual('serial', self.messages[0]['port'])
        self.assertEqual('AABBCCDD', self.messages[0]['value'])

    def test_x90_wellformed(self):
        self.serial.feed('900013a20040401122012340' + binascii.hexlify('status:1\n'.encode()).decode()) # Receive well-formed serial packet
        self.wait()
        self.assertEqual(1, len(self.messages))
        self.assertEqual('0013a20040401122', self.messages[0]['address'])
        self.assertEqual('status', self.messages[0]['port'])
        self.assertEqual('1', self.messages[0]['value'])

    def test_x92(self):
        self.serial.feed('920013a200406bfd090123010110008010000B00')  # IO Sample DIO12:1, ADC7(Supply Voltage):2816
        self.wait()
        self.assertEqual(2, len(self.messages))
        self.assertEqual('0013a200406bfd09', self.messages[0]['address'])
        self.assertEqual('adc-7', self.messages[1]['port'])
        self.assertEqual(2816, self.messages[1]['value'])
        self.assertEqual('0013a200406bfd09', self.messages[1]['address'])
        self.assertEqual('dio-12', self.messages[0]['port'])
        self.assertEqual(1, self.messages[0]['value'])

    def test_x88_node_discovery(self):
        # ND reply from DigiMesh node XBEE_A, captured from real hardware
        discovered = []
        self.xbee.on_node_discovery = lambda address, alias: discovered.append((address, alias))
        self.serial.feed('8801' + binascii.hexlify(b'ND').decode() + '00' +
                         'fffe' + '0013a2004097668a' + binascii.hexlify(b'XBEE_A').decode() + '00' +
                         'fffe' + '01' + '00' + 'c105' + '101e')
        self.wait(lambda: discovered)
        self.assertEqual([('0013a2004097668a', 'XBEE_A')], discovered)
        # Daemon must answer by setting the IO sample rate (IR) on the node
        self.assertIn(b'IR', self.serial.data)

    def test_x97_pin_config(self):
        # Remote AT response: D3 configured as digital input (3)
        self.serial.feed('9741' + '0013a2004097668a' + 'fffe' +
                         binascii.hexlify(b'D3').decode() + '00' + '03')
        self.wait()
        self.assertEqual(1, len(self.messages))
        self.assertEqual('0013a2004097668a', self.messages[0]['address'])
        self.assertEqual('pin-3', self.messages[0]['port'])
        self.assertEqual(3, self.messages[0]['value'])

if __name__ == '__main__':
    unittest.main()
