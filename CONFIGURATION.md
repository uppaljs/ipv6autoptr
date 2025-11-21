# IPv6 Auto PTR Server - Configuration Guide

This document describes the comprehensive configuration system for the IPv6 Auto PTR DNS server, which supports multiple configuration sources with a clear priority order.

## Configuration Priority Order

The configuration system follows this priority order (highest to lowest):

1. **Command Line Arguments** (highest priority)
2. **Environment Variables** (with `IPV6AUTOPTR_` prefix)
3. **Configuration File** (YAML format)
4. **Built-in Defaults** (lowest priority)

## Configuration File (config.yaml)

The server uses a YAML configuration file for structured configuration. The default file is `config.yaml`, but you can specify a different file using the `--config` argument.

### Example Configuration File

```yaml
# IPv6 Auto PTR Server Configuration
# This file contains all configurable options for the IPv6 PTR DNS server.
# Environment variables with prefix IPV6AUTOPTR_ can override these settings.
# Command line arguments take highest precedence.

# Server Configuration
server:
  # Port to listen on (default: 5353)
  port: 5353

  # Address to bind to (default: '::' for IPv6, '0.0.0.0' for IPv4)
  bind_address: "::"

  # Enable TCP server (default: false)
  enable_tcp: false

  # Enable UDP server (default: true)
  enable_udp: true

  # Verbosity level (0-3, default: 0)
  verbose: 0

# DNS Configuration
dns:
  # TTL for DNS responses in seconds (default: 86400 = 24 hours)
  ttl: 86400

  # Domain suffix for auto-generated PTR records
  domain_suffix: "ip6.example.com."

  # Maximum number of worker threads for processing requests
  max_workers: 32

# IPv6 Configuration
ipv6:
  # List of IPv6 subnets to handle PTR queries for
  # Only addresses within these subnets will get auto-generated PTR records
  subnets:
    - "2001:db8:1::/48"
    - "2001:db8:2::/64"

# PTR Records Configuration
ptr_records:
  # Path to the custom PTR records configuration file
  config_file: "ipv6autoptr.conf"

  # Whether to use custom PTR records from config file (default: true)
  use_custom: true

# Logging Configuration
logging:
  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: "INFO"

  # Log format
  format: "%(asctime)s - %(levelname)s - %(message)s"

  # Log file path (optional, logs to console if not specified)
  file: null
```

## Environment Variables

All configuration options can be overridden using environment variables with the `IPV6AUTOPTR_` prefix.

### Available Environment Variables

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `IPV6AUTOPTR_PORT` | integer | 5353 | Server port |
| `IPV6AUTOPTR_BIND_ADDRESS` | string | "::" | Bind address (IPv6/IPv4) |
| `IPV6AUTOPTR_ENABLE_TCP` | boolean | false | Enable TCP server |
| `IPV6AUTOPTR_ENABLE_UDP` | boolean | true | Enable UDP server |
| `IPV6AUTOPTR_VERBOSE` | integer | 0 | Verbosity level (0-3) |
| `IPV6AUTOPTR_TTL` | integer | 86400 | DNS response TTL in seconds |
| `IPV6AUTOPTR_DOMAIN_SUFFIX` | string | "ip6.example.com." | Domain suffix for auto PTR records |
| `IPV6AUTOPTR_MAX_WORKERS` | integer | 32 | Maximum worker threads |
| `IPV6AUTOPTR_SUBNETS` | string | "2001:db8:1::/48,2001:db8:2::/64" | Comma-separated list of IPv6 subnets |
| `IPV6AUTOPTR_PTR_CONFIG_FILE` | string | "ipv6autoptr.conf" | Path to PTR records config file |
| `IPV6AUTOPTR_USE_CUSTOM_PTR` | boolean | true | Enable custom PTR records |
| `IPV6AUTOPTR_LOG_LEVEL` | string | "INFO" | Log level |
| `IPV6AUTOPTR_LOG_FORMAT` | string | "%(asctime)s - %(levelname)s - %(message)s" | Log format |
| `IPV6AUTOPTR_LOG_FILE` | string | null | Log file path |

### Boolean Environment Variables

Boolean values can be set using any of these formats:
- `true`, `yes`, `1`, `on`, `enable` → True
- `false`, `no`, `0`, `off`, `disable` → False

## Command Line Arguments

The server accepts the following command line arguments:

```
usage: ipv6autoptr.py [-h] [--port PORT] [--tcp] [--udp] [--verbose]
                      [--config CONFIG]

Start a IPV6AUTOPTR implemented in Python.

options:
  -h, --help       show this help message and exit
  --port PORT      The port to listen on.
  --tcp            Listen to TCP connections.
  --udp            Listen to UDP datagrams.
  --verbose        Increase verbosity
  --config CONFIG  Configuration file path.
```

## Configuration Examples

### Example 1: Basic Configuration

**File**: `config.yaml`
```yaml
server:
  port: 53
  bind_address: "::"
  enable_udp: true

dns:
  domain_suffix: "ip6.mydomain.com."
  ttl: 3600

ipv6:
  subnets:
    - "2001:db8:1000::/48"
```

**Usage**:
```bash
python ipv6autoptr.py --config config.yaml
```

### Example 2: Environment Variables (Docker)

```bash
export IPV6AUTOPTR_PORT=53
export IPV6AUTOPTR_DOMAIN_SUFFIX="ip6.docker.local."
export IPV6AUTOPTR_SUBNETS="2001:db8:1000::/48,2001:db8:2000::/64"
export IPV6AUTOPTR_VERBOSE=2

python ipv6autoptr.py --udp
```

### Example 3: Production Configuration

**File**: `production.yaml`
```yaml
server:
  port: 53
  bind_address: "::"
  enable_udp: true
  enable_tcp: true
  verbose: 1

dns:
  domain_suffix: "ip6.company.com."
  ttl: 86400
  max_workers: 64

ipv6:
  subnets:
    - "2001:db8:1000::/32"  # Company IPv6 range

ptr_records:
  config_file: "/etc/ipv6autoptr/custom-records.conf"

logging:
  level: "WARNING"
  format: "%(asctime)s [%(levelname)s] %(message)s"
  file: "/var/log/ipv6autoptr.log"
```

### Example 4: Development Configuration

**Environment Variables**:
```bash
export IPV6AUTOPTR_PORT=5353
export IPV6AUTOPTR_BIND_ADDRESS="127.0.0.1"
export IPV6AUTOPTR_VERBOSE=3
export IPV6AUTOPTR_LOG_LEVEL="DEBUG"
```

**Usage**:
```bash
python ipv6autoptr.py --udp --verbose
```

## Docker Configuration

### Using Environment Variables

```bash
docker run -d \
  --name ipv6autoptr \
  -p 53:53/udp \
  -e IPV6AUTOPTR_PORT=53 \
  -e IPV6AUTOPTR_DOMAIN_SUFFIX="ip6.example.com." \
  -e IPV6AUTOPTR_SUBNETS="2001:db8:1::/48,2001:db8:2::/64" \
  -e IPV6AUTOPTR_VERBOSE=1 \
  ipv6autoptr:latest
```

### Using Docker Compose

See `docker-compose.yml` for complete examples with different configurations.

### Using Custom Configuration File

```bash
docker run -d \
  --name ipv6autoptr \
  -p 53:53/udp \
  -v ./my-config.yaml:/app/config.yaml:ro \
  -v ./my-ptr-records.conf:/app/ipv6autoptr.conf:ro \
  ipv6autoptr:latest
```

## Custom PTR Records

The server supports custom PTR records through a separate configuration file. The format is:

```
# Custom PTR Records Configuration
# Format: <ipv6-address-in-arpa-format> = <custom-ptr-domain-name>

# Example for 2001:db8:1::1 -> custom-server.example.com
1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa. = custom-server.example.com.

# Example for 2001:db8:2::5 -> mail.example.com
5.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.2.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa. = mail.example.com.
```

## Troubleshooting

### Common Configuration Issues

1. **Port binding errors**: Check if the port is already in use or if you have permission to bind to the port (especially port 53).

2. **IPv6 binding issues**: Some systems may have IPv6 disabled. Try using `0.0.0.0` for IPv4-only binding.

3. **File permissions**: Ensure the configuration files are readable by the user running the server.

4. **YAML syntax errors**: Validate your YAML configuration file syntax.

### Debugging Configuration

1. **Check loaded configuration**:
   ```python
   from ipv6autoptr import Config
   config = Config('config.yaml')
   print(f"Port: {config.port}")
   print(f"Domain: {config.domain_suffix}")
   print(f"Subnets: {config.subnets}")
   ```

2. **Verbose logging**: Use `--verbose` or `IPV6AUTOPTR_VERBOSE=3` for detailed logging.

3. **Test configuration**: Start the server on a non-privileged port first to test configuration.

## Migration from Hardcoded Configuration

If you're upgrading from a version with hardcoded configuration:

1. **Backup your changes**: Save any modifications you made to the hardcoded values.

2. **Create config.yaml**: Use the example configuration file and customize it with your values.

3. **Test the configuration**: Start the server with `--verbose` to verify configuration loading.

4. **Update deployment scripts**: Modify your deployment scripts to use environment variables or configuration files.

## Security Considerations

1. **File permissions**: Ensure configuration files have appropriate read permissions.

2. **Environment variables**: Be careful when using environment variables in shared environments.

3. **Docker secrets**: For production Docker deployments, consider using Docker secrets for sensitive configuration.

4. **Network binding**: Use specific bind addresses instead of `0.0.0.0` or `::` when possible for security.