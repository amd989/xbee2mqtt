#!/bin/bash

set -e

FOLDER=$(dirname $(realpath $0))/.venv
PIP=$FOLDER/bin/pip
PYTHON=$FOLDER/bin/python

if [ $# -eq 0 ]; then
    ACTION='activate'
else
    ACTION=$1
fi

case "$ACTION" in

    "setup")
        if [ ! -d $FOLDER ]; then
            python3 -m venv $FOLDER
        fi

        $PIP install --upgrade pyyaml
        $PIP install --upgrade pyserial
        $PIP install --upgrade pytest
        $PIP install --upgrade paho-mqtt
	$PIP install --upgrade parse
	$PIP install --upgrade xbee
        ;;

    "start" | "stop" | "restart")
        $PYTHON xbee2mqtt.py $ACTION
        ;;

    "tests")
        $PYTHON -m pytest tests/ -v
        ;;

    "console")
        $PYTHON xbee2console.py
        ;;

    *)
        echo "Unknown action $ACTION."
        ;;
esac


