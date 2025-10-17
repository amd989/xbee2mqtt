#!/bin/bash

set -e

FOLDER=$(dirname $(realpath $0))/.venv
PIP=$FOLDER/bin/pip
PYTHON=$FOLDER/bin/python

if [ $# -eq 0 ]; then
    echo "Usage: ./do <action>"
    echo ""
    echo "Native Python actions:"
    echo "  setup      - Create virtualenv and install dependencies"
    echo "  start      - Start daemon in native mode"
    echo "  stop       - Stop daemon"
    echo "  restart    - Restart daemon"
    echo "  tests      - Run pytest tests"
    echo "  console    - Run xbee2console.py for debugging"
    echo ""
    echo "Docker actions:"
    echo "  build      - Build Docker image"
    echo "  up         - Start Docker container with docker-compose"
    echo "  down       - Stop Docker container"
    echo "  logs       - View Docker container logs"
    echo "  shell      - Open shell in running container"
    exit 0
fi

ACTION=$1

case "$ACTION" in

    "setup")
        if [ ! -d $FOLDER ]; then
            python3 -m venv $FOLDER
        fi
        echo "Installing dependencies from requirements.txt..."
        $PIP install --upgrade pip
        $PIP install -r requirements.txt
        echo "Setup complete! Virtualenv created at $FOLDER"
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

    "build")
        docker build -t xbee2mqtt:latest .
        echo "Docker image built successfully!"
        ;;

    "up")
        docker-compose -f docker-compose.dev.yml up -d
        echo "Container started. Use './do logs' to view logs."
        ;;

    "down")
        docker-compose -f docker-compose.dev.yml down
        echo "Container stopped."
        ;;

    "logs")
        docker-compose -f docker-compose.dev.yml logs -f
        ;;

    "shell")
        docker-compose -f docker-compose.dev.yml exec xbee2mqtt /bin/bash
        ;;

    "rebuild")
        docker-compose -f docker-compose.dev.yml down
        docker build -t xbee2mqtt:latest .
        docker-compose -f docker-compose.dev.yml up -d
        echo "Container rebuilt and started. Use './do logs' to view logs."
        ;;

    *)
        echo "Unknown action '$ACTION'."
        echo "Run './do' without arguments to see available actions."
        exit 1
        ;;
esac


