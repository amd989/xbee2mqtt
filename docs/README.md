# xbee2mqtt Documentation

This directory contains comprehensive documentation for the xbee2mqtt project.

## Table of Contents

### Quick Start
- **[../README.md](../README.md)** - Main README with quick start and overview

### Deployment Guides
- **[README.docker.md](README.docker.md)** - Complete Docker deployment guide
  - Docker installation and configuration
  - Building and running containers
  - Serial device mapping
  - Troubleshooting
  - Production deployment tips

- **[RASPBERRY_PI.md](RASPBERRY_PI.md)** - Raspberry Pi specific setup
  - USB and GPIO UART connection options
  - Pin wiring diagrams
  - UART configuration and setup
  - Model-specific notes (Pi 3/4/5 vs Zero/1/2)
  - Performance optimization
  - Complete setup examples

### Development
- **[CLAUDE.md](CLAUDE.md)** - Architecture and development guide
  - Project architecture overview
  - Component interactions
  - Message flow diagrams
  - Configuration system
  - Development commands
  - Testing procedures

- **[TESTING.md](TESTING.md)** - Comprehensive testing guide
  - Verification scripts
  - Unit testing with pytest
  - Integration testing
  - Docker testing
  - Troubleshooting test failures

## Quick Links by Use Case

### I want to...

**Deploy with Docker**
→ Start with [README.docker.md](README.docker.md)

**Deploy on Raspberry Pi**
→ Start with [RASPBERRY_PI.md](RASPBERRY_PI.md)

**Understand the architecture**
→ Read [CLAUDE.md](CLAUDE.md)

**Verify Python 3 migration**
→ See [TESTING.md](TESTING.md)

**Configure XBee and MQTT**
→ See main [README.md](../README.md#configuration)

## File Overview

| File | Purpose | Audience |
|------|---------|----------|
| CLAUDE.md | Architecture, components, development | Developers, contributors |
| README.docker.md | Docker deployment | DevOps, production deployments |
| RASPBERRY_PI.md | Raspberry Pi setup | IoT enthusiasts, home automation |
| TESTING.md | Testing procedures | Developers, QA |

## Contributing

When adding documentation:
1. Place it in this `docs/` directory
2. Update this README.md with a link
3. Update the main [README.md](../README.md) Documentation section
4. Use clear headings and code examples
5. Include troubleshooting sections where applicable

## Support

For questions or issues:
1. Check the relevant documentation guide above
2. Review troubleshooting sections in each guide
3. Run `python verify_migration.py` to check for setup issues
4. Open an issue on the repository

---

**Note**: Keep the main [README.md](../README.md) concise and user-focused. Detailed technical documentation belongs in this `docs/` directory.
