Name:           xbee2mqtt
Version:        %{_version}
Release:        1%{?dist}
Summary:        XBee ZigBee to MQTT gateway
License:        GPL-3.0-or-later
URL:            https://github.com/amd989/xbee2mqtt
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

# The code and the Python packages it needs live in /usr/lib/xbee2mqtt as
# plain folders (see packaging/build-lib.sh), all pure Python. Keep rpm's
# helpers away from them: no shebang rewriting or byte-compiling for the
# build host's Python, and the bundled packages provide nothing to the rest
# of the system.
%global __brp_mangle_shebangs_exclude_from ^%{_prefix}/lib/xbee2mqtt/
%global __brp_python_bytecompile %{nil}
%global __provides_exclude_from ^%{_prefix}/lib/xbee2mqtt/
%global __requires_exclude_from ^%{_prefix}/lib/xbee2mqtt/

BuildRequires:  python3 >= 3.9
BuildRequires:  systemd-rpm-macros

Requires:       python3 >= 3.9
Requires(pre):  shadow-utils
Recommends:     alejandro-md-release
%{?systemd_requires}

%description
Watches a coordinator XBee radio in API mode on a serial port, publishes what
the remote radios report to an MQTT broker, and sets their digital pins from
MQTT messages. Can announce the radios to Home Assistant through MQTT
discovery.

Runs as the xbee2mqtt systemd service, which is installed but not enabled.
Edit /etc/xbee2mqtt/xbee2mqtt.yaml, then run
`sudo systemctl enable --now xbee2mqtt`. xbee2mqtt-probe finds the baud rate
and mode a radio answers on.

%prep
%setup -q

%build

%install
sh packaging/build-lib.sh %{buildroot}%{_prefix}/lib/xbee2mqtt
install -D -m 0755 packaging/xbee2mqtt %{buildroot}%{_bindir}/xbee2mqtt
install -D -m 0755 packaging/xbee2mqtt-probe %{buildroot}%{_bindir}/xbee2mqtt-probe
install -D -m 0644 packaging/xbee2mqtt.service %{buildroot}%{_unitdir}/xbee2mqtt.service
install -D -m 0640 config/xbee2mqtt.yaml.sample %{buildroot}%{_sysconfdir}/xbee2mqtt/xbee2mqtt.yaml

%files
%license LICENSE
%doc README.md CHANGELOG.md
%{_bindir}/xbee2mqtt
%{_bindir}/xbee2mqtt-probe
%{_prefix}/lib/xbee2mqtt
%{_unitdir}/xbee2mqtt.service
%dir %{_sysconfdir}/xbee2mqtt
# Holds the MQTT password
%attr(0640,root,xbee2mqtt) %config(noreplace) %{_sysconfdir}/xbee2mqtt/xbee2mqtt.yaml

%pre
getent group xbee2mqtt >/dev/null || groupadd -r xbee2mqtt
getent passwd xbee2mqtt >/dev/null || \
    useradd -r -g xbee2mqtt -d / -s /sbin/nologin \
        -c "XBee to MQTT gateway" xbee2mqtt
# Serial ports belong to dialout
usermod -a -G dialout xbee2mqtt
exit 0

%post
# Installed but not enabled, whatever the presets say: the default config
# points at /dev/ttyUSB0 and a broker on localhost, which may not be right.
systemctl daemon-reload >/dev/null 2>&1 || :
if [ "$1" -eq 1 ]; then
    echo "xbee2mqtt installed. Set the serial port and MQTT broker in %{_sysconfdir}/xbee2mqtt/xbee2mqtt.yaml,"
    echo "then start it with: sudo systemctl enable --now xbee2mqtt"
fi

%preun
%systemd_preun xbee2mqtt.service
# Written by %%posttrans, so not in the package's file list
find %{_prefix}/lib/xbee2mqtt -name __pycache__ -type d -prune \
    -exec rm -rf {} + 2>/dev/null || :

%postun
%systemd_postun_with_restart xbee2mqtt.service

%posttrans
# Byte-compile for whichever Python 3 this system has. In %%posttrans so an
# upgrade's old %%preun can't run after it.
python3 -m compileall -q %{_prefix}/lib/xbee2mqtt >/dev/null 2>&1 || :

%changelog
