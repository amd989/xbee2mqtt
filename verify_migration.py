#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for Python 3 migration
This script checks that all Python files can be imported and basic syntax is correct
"""

import sys
import py_compile
import os

# Handle Windows console encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_python_version():
    """Verify Python 3.6+ is being used"""
    if sys.version_info < (3, 6):
        print("❌ ERROR: Python 3.6+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    dependencies = [
        ('yaml', 'pyyaml'),
        ('serial', 'pyserial'),
        ('paho.mqtt.client', 'paho-mqtt'),
        ('parse', 'parse'),
        ('xbee', 'xbee'),
        ('pytest', 'pytest'),
    ]

    all_ok = True
    print("\nChecking dependencies:")
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - NOT INSTALLED")
            all_ok = False

    return all_ok

def check_syntax():
    """Compile all Python files to check for syntax errors"""
    print("\nChecking Python syntax:")

    files_to_check = [
        'xbee2mqtt.py',
        'xbee2console.py',
        'libs/config.py',
        'libs/daemon.py',
        'libs/filters.py',
        'libs/processor.py',
        'libs/xbee_wrapper.py',
        'libs/mosquitto_wrapper.py',
    ]

    all_ok = True
    for filepath in files_to_check:
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✅ {filepath}")
        except py_compile.PyCompileError as e:
            print(f"❌ {filepath} - SYNTAX ERROR")
            print(f"   {e}")
            all_ok = False
        except FileNotFoundError:
            print(f"⚠️  {filepath} - FILE NOT FOUND")

    return all_ok

def check_imports():
    """Try importing main modules"""
    print("\nChecking module imports:")

    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    modules = [
        ('libs.config', 'Config'),
        ('libs.processor', 'Processor'),
        ('libs.filters', 'FilterFactory'),
        ('libs.mosquitto_wrapper', 'MosquittoWrapper'),
        ('libs.xbee_wrapper', 'XBeeWrapper'),
        ('libs.daemon', 'Daemon'),
    ]

    all_ok = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name} - IMPORT ERROR")
            print(f"   {e}")
            all_ok = False

    return all_ok

def check_python2_patterns():
    """Scan for common Python 2 patterns that should be migrated"""
    print("\nScanning for Python 2 patterns:")

    import re

    patterns = {
        r'\.iteritems\(\)': '.iteritems() (should be .items())',
        r'\.iterkeys\(\)': '.iterkeys() (should be .keys())',
        r'\.itervalues\(\)': '.itervalues() (should be .values())',
        r'except\s+\w+\s*,\s*\w+:': 'except X, e: (should be except X as e:)',
        r'print\s+["\']': 'print "text" (should be print("text"))',
        r'\bfile\s*\(': 'file() (should be open())',
    }

    files_to_scan = [
        'xbee2mqtt.py',
        'xbee2console.py',
        'libs/config.py',
        'libs/daemon.py',
        'libs/filters.py',
        'libs/processor.py',
        'libs/xbee_wrapper.py',
        'libs/mosquitto_wrapper.py',
    ]

    issues_found = 0
    for filepath in files_to_scan:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern, description in patterns.items():
                    matches = re.findall(pattern, content)
                    if matches:
                        print(f"⚠️  {filepath}: Found {description}")
                        issues_found += len(matches)
        except FileNotFoundError:
            pass

    if issues_found == 0:
        print("✅ No Python 2 patterns detected")
        return True
    else:
        print(f"❌ Found {issues_found} potential Python 2 patterns")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Python 3 Migration Verification")
    print("=" * 60)

    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Syntax Check": check_syntax(),
        "Module Imports": check_imports(),
        "Python 2 Patterns": check_python2_patterns(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check_name:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All checks passed! Migration looks good.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
