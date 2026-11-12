#!/usr/bin/env python3
"""
XBee serial diagnostic.

Finds the baud rate and mode an XBee answers on, then prints its firmware,
network and pin settings. A loopback mode checks the serial adapter (or the
Pi UART) on its own.

Stop xbee2mqtt first, since it holds the serial port.

Examples:
    python tools/xbee_probe.py /dev/serial0
    python tools/xbee_probe.py COM5 --baud 9600
    python tools/xbee_probe.py /dev/ttyUSB0 --loopback   # jumper TX to RX, no XBee
"""
import argparse
import sys
import time

import serial

BAUDS = [9600, 115200, 57600, 38400, 19200, 4800, 2400, 1200, 230400]

SETTINGS = [
    ("HV", "hardware version"),
    ("VR", "firmware version"),
    ("DD", "device type"),
    ("NI", "node identifier"),
    ("SH", "serial number high"),
    ("SL", "serial number low"),
    ("AP", "API mode (0=transparent, 1=API, 2=API escaped)"),
    ("BD", "baud rate (3=9600, 7=115200)"),
    ("ID", "network ID"),
    ("CH", "channel"),
    ("CE", "coordinator / routing role"),
    ("AI", "association indicator (0=ok)"),
    ("SM", "sleep mode (0=off)"),
    ("IR", "IO sample rate (ms, hex)"),
    ("IC", "digital change detection mask"),
    ("D6", "RTS (0=off, 1=flow control)"),
    ("D7", "CTS (0=off, 1=flow control)"),
    ("PL", "power level"),
    ("DB", "RSSI of last received packet"),
]
PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D8", "D9", "P0", "P1", "P2"]


def api_frame(command, frame_id=1):
    data = bytes([0x08, frame_id]) + command.encode()
    return bytes([0x7E, 0, len(data)]) + data + bytes([0xFF - (sum(data) & 0xFF)])


def read_for(port, seconds):
    deadline = time.time() + seconds
    buf = b""
    while time.time() < deadline:
        buf += port.read(port.in_waiting or 1)
    return buf


def open_port(name, baud):
    # No flow control: the XBee ignores RTS/CTS unless D6/D7 enable them
    return serial.Serial(name, baud, timeout=0.02, rtscts=False, xonxoff=False)


def enter_command_mode(port):
    port.reset_input_buffer()
    time.sleep(1.1)  # guard time before +++
    port.write(b"+++")
    return read_for(port, 2.2).startswith(b"OK")


def detect(name, bauds):
    """Return (baud, mode) the radio answers on, or (None, None)."""
    for baud in bauds:
        with open_port(name, baud) as port:
            port.reset_input_buffer()
            port.write(api_frame("VR"))
            reply = read_for(port, 0.5)
            if reply.startswith(b"\x7e"):
                print(f"  {baud:>6}: API frame reply {reply.hex()}")
                return baud, "api"
            if enter_command_mode(port):
                print(f"  {baud:>6}: answered +++ (AT command mode)")
                port.write(b"ATCN\r")
                return baud, "at"
            print(f"  {baud:>6}: {'garbage ' + reply.hex() if reply else 'no reply'}")
    return None, None


def read_settings(name, baud):
    with open_port(name, baud) as port:
        if not enter_command_mode(port):
            print("Could not enter command mode to read settings.")
            return
        try:
            for command, label in SETTINGS:
                port.write(f"AT{command}\r".encode())
                value = read_for(port, 0.4).strip().decode(errors="replace")
                print(f"  {command}  {value:<12} {label}")
            values = []
            for pin in PINS:
                port.write(f"AT{pin}\r".encode())
                values.append(f"{pin}={read_for(port, 0.4).strip().decode(errors='replace')}")
            print("  pins " + " ".join(values))
            print("       (0=off, 2=ADC, 3=digital in, 4=out low, 5=out high)")
        finally:
            port.write(b"ATCN\r")
            read_for(port, 0.3)


def loopback(name, baud):
    pattern = bytes(range(256))
    with open_port(name, baud) as port:
        port.reset_input_buffer()
        port.write(pattern)
        echoed = read_for(port, 1.0 + len(pattern) * 10 / baud)
    if echoed == pattern:
        print(f"Loopback OK: {len(pattern)} bytes echoed at {baud} baud.")
        return 0
    print(f"Loopback FAILED: sent {len(pattern)} bytes, got {len(echoed)} back.")
    if not echoed:
        print("Nothing came back: check the TX-RX jumper, or the port is not wired out.")
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("port", help="serial port, e.g. /dev/serial0, /dev/ttyUSB0, COM5")
    parser.add_argument("--baud", type=int, action="append", help="baud rate to try (repeatable); default tries common rates")
    parser.add_argument("--loopback", action="store_true", help="adapter self-test with TX jumpered to RX, no XBee attached")
    args = parser.parse_args()

    try:
        if args.loopback:
            return loopback(args.port, (args.baud or [9600])[0])

        print(f"Looking for an XBee on {args.port}...")
        baud, mode = detect(args.port, args.baud or BAUDS)
        if not baud:
            print("\nNo reply at any baud rate. Check, in order:")
            print("  1. DIN/DOUT orientation: XBee DOUT goes to the host RX, DIN to the host TX")
            print("  2. 3.3V and GND at the XBee, and that the module is seated")
            print("  3. the host side on its own, with --loopback")
            return 1

        print(f"\nRadio found at {baud} baud ({mode} mode). Settings:")
        read_settings(args.port, baud)
        return 0
    except serial.SerialException as exc:
        print(f"Serial error: {exc}")
        print("Check the port name, and that xbee2mqtt (or another program) isn't holding it.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
