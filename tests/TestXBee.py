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

    def wait(self):
        while len(self.messages) == 0:
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

if __name__ == '__main__':
    unittest.main()
