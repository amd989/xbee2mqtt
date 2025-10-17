## What's Changed
* ci: :construction_worker: add automatic version tagging by @amd989

## What's Changed in 0.8.20251017
* fix: 🐛 correct mqtt connectivity issues by @amd989
* ci: :construction_worker: add support for docker image publish by @amd989
* docs: :memo: add documentation by @amd989
* feat: :sparkles: add docker image support by @amd989
* refactor(python): :recycle: migrate to python 3.9 by @amd989
* escape uart connection for Xbee. use mqtt pattern whatsoever. by @moustik

### New Contributors
* @amd989 made their first contribution
* @moustik made their first contribution

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.7.20160903...v0.8.20251017

## What's Changed in 0.7.20160903
* Bump to version 0.7.20160903 by @ehbello
* Add default_output_topic_patern parameter equivalent to old default_topic_pattern. by @ehbello
* Unsubscribes digital topics if the pin configuration is changed to a non-digital input. by @ehbello
* Publish alias name on XBee identification. by @ehbello
* Added change_detection to config IO Digital Change Detection of nodes. by @ehbello
* Added sample_rate parameter to config IO Sample Rate of nodes. by @ehbello
* Considerate pins>9 for Px command responses received. by @ehbello
* Set 'None' to variables if requested packet field does not exists. by @ehbello
* Added 1 sec delay after each command while querying the status of XBee's ports. by @ehbello
* Fixed some errors parsing topics from/to new schema. by @ehbello
* Fixed transformation of raw input MQTT topics on received messages. by @ehbello
* Limited values of send_message method for digital (dio) outputs. by @ehbello
* Don't process AT command responses if status is not OK. by @ehbello
* Added error_callback to XBeeWrapper and logged tracebacks to debug better by @ehbello

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.6.20160829...v0.7.20160903

## What's Changed in 0.6.20160829
* Bump to version 0.6.20160829 by @ehbello
* Catch SerialException if serial port is not available. by @ehbello
* XBee send_message now supports to set pin configuration. by @ehbello
* Accepts {item} tag in default_topic_pattern to expand port acronyms by @ehbello
* Subscribe to input topics automatically when undefined topics are exposed by @ehbello
* Add feature to query pins configuration on node discovery. by @ehbello
* Added handle of ZigBee Remote Command Responses. by @ehbello
* Initial aproach to Node Discovery feature. by @ehbello

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.5.20160815...v0.6.20160829

## What's Changed in 0.5.20160815
* Bump to version 0.5.20160815 by @ehbello
* Support for official python-xbee library (>=2.1.0) and XBee Series2 modules by @ehbello
* Fixed some configuration keys related to the daemon and debugging by @ehbello
* Added support for username and password on MQTT connection by @ehbello
* Added support for paho-mqtt instad of old mosquitto library by @ehbello
* Refactorized (and fixed) 'do' script to get working again by @ehbello
* Small changes imported from production
* Link to the post about this utility. by @xoseperez
* Moved find_devices to xbee_wrapper
* Added nose to do script
* Migrate xbee2console to use logging library
* Adding reload feature to daemon class

### New Contributors
* @ehbello made their first contribution

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.4.20130708...v0.5.20160815

## What's Changed in 0.4.20130708
* Moved to virtual environment and 1.X MQTT library
* Configuration files moved to config folder
* Fix mosquitto.py version update incompatibilities by @xoseperez
* Added chained filters
* Fix casting issues in filters

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.3.1...v0.4.20130708

## What's Changed in 0.3.1
* Catch python-xbee exceptions
* Update documentation

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.3...v0.3.1

## What's Changed in 0.3
* Added option to set remote radio digital output ports LOW or HIGH
* Fix some configuration issues
* Added regexp filter by @xoseperez
* Fix tests (shame on me)
* Updating documentation
* Simplify routing
* Added string format filter
* Merge by @xoseperez
* Removing duplicate messages
* Changing lineal filter to output integer
* Merge branch 'master' of https://github.com/xoseperez/xbee2mqtt
* Improved unit test suite

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.2.1...v0.3

## What's Changed in 0.2.1
* Documentation and licensing by @xoseperez
* Do not set will by default by @xoseperez
* Added tests for all existing filters by @xoseperez
* New tests by @xoseperez
* Setting up unit testing by @xoseperez
* Some clean up by @xoseperez
* Fill refactoring and deeper dependency injection by @xoseperez
* Added filters: linear, boolean, not, enum; publish and timestampable flags
* Added sample configuration file by @xoseperez
* Merge branch 'master' of https://github.com/xoseperez/xbee2mqtt
* Added requirements to README file by @xoseperez
* Change log format by @xoseperez
* Refactor into libs
* Small changes by @xoseperez
* Refactor config file to make it more readable by @xoseperez
* Renaming device:sensor to address:port by @xoseperez
* Added mapping functionality by @xoseperez

**Full Changelog**: https://github.com/amd989/xbee2mqtt/compare/v0.2...v0.2.1

## What's Changed in 0.2
* Refactor to apply dependency injection pattern by @xoseperez
* Suport for frame type 0x92, IO samples by @xoseperez
* Adding debugging messages
* Dummy serial, better handling split serial data and some logging
* Added xbee folder to gitignore. Eases debugging the xbee library
* Fix variable type and cleanup method by @xoseperez
* Fix bug and some renaming by @xoseperez
* Deleted xbee library, it's forked in https://xose.perez@code.google.com/r/xoseperez-python-xbee/ by @xoseperez
* Removed unused and non needed files
* Added disconnect method
* Initial commit by @xoseperez

### New Contributors
* @xoseperez made their first contribution
* @ made their first contribution

<!-- generated by git-cliff -->
