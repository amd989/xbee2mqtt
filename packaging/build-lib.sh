#!/bin/sh
# Install xbee2mqtt and the Python packages it needs into one folder (DEST),
# for the deb and rpm packages. Usage: build-lib.sh DEST
#
# The code goes into DEST and its dependencies into DEST/vendor. python-xbee
# isn't packaged by Debian or Fedora, and Trixie only has paho-mqtt 2, so the
# dependencies ship with xbee2mqtt. They go into a plain folder rather than a
# virtualenv: a venv is tied to the Python it was made with, and one package
# has to work on every release (Python 3.9 on EL9, 3.11 on Bookworm, 3.13 on
# Trixie).
#
# Everything here is pure Python, which is also why the packages are
# Architecture: all and noarch. Build with the oldest Python to support
# (Python 3.9), so pip picks versions that still run on it.
set -eu

[ $# -eq 1 ] || { echo "Usage: $0 DEST" >&2; exit 2; }
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$1"
PYTHON="${PYTHON:-python3}"

venv="$(mktemp -d)"
trap 'rm -rf "$venv"' EXIT
"$PYTHON" -m venv "$venv"
"$venv/bin/pip" install -q --disable-pip-version-check --upgrade pip

# requirements.txt also lists the test tools
grep -v -i '^pytest' "$SRC/requirements.txt" > "$venv/requirements.txt"

# .pyc files are written on the target by the package's postinst, for the
# Python that's there.
mkdir -p "$DEST/vendor"
"$venv/bin/pip" install -q --disable-pip-version-check --no-compile \
    --no-warn-script-location --target "$DEST/vendor" \
    -r "$venv/requirements.txt"

# PyYAML's wheel carries a C loader built for one Python version. Without it
# PyYAML uses its pure Python loader, which is all xbee2mqtt asks for
# (yaml.SafeLoader).
rm -f "$DEST"/vendor/yaml/_yaml*.so

# Console scripts point at the build venv
rm -rf "$DEST/vendor/bin"

install -m 0644 "$SRC/xbee2mqtt.py" "$SRC/docker-entrypoint.py" "$DEST/"
install -d "$DEST/libs" "$DEST/tools"
install -m 0644 "$SRC"/libs/*.py "$DEST/libs/"
install -m 0644 "$SRC/tools/xbee_probe.py" "$DEST/tools/"

find "$DEST" -name __pycache__ -type d -prune -exec rm -rf {} +

# Anything compiled would tie the package to one Python and one architecture
bad="$(find "$DEST" -name '*.so')"
if [ -n "$bad" ]; then
    echo "Compiled extension modules in $DEST:" >&2
    echo "$bad" >&2
    exit 1
fi
