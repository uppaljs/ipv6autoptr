# IPv6 Auto PTR DNS Server Dockerfile
FROM python:3.13-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    bind-tools \
    iputils \
    net-tools

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .
COPY *.conf .
COPY config.yaml .

# Create non-root user for security
RUN addgroup -g 1001 ipv6autoptr && \
    adduser -D -u 1001 -G ipv6autoptr ipv6autoptr

# Change ownership of app files
RUN chown -R ipv6autoptr:ipv6autoptr /app

# Switch to non-root user
USER ipv6autoptr

# Environment variables with defaults
ENV IPV6AUTOPTR_PORT=53
ENV IPV6AUTOPTR_BIND_ADDRESS="::"
ENV IPV6AUTOPTR_ENABLE_UDP=true
ENV IPV6AUTOPTR_ENABLE_TCP=false
ENV IPV6AUTOPTR_VERBOSE=1
ENV IPV6AUTOPTR_TTL=86400
ENV IPV6AUTOPTR_DOMAIN_SUFFIX="ip6.docker.local."
ENV IPV6AUTOPTR_MAX_WORKERS=32
ENV IPV6AUTOPTR_SUBNETS="2001:db8:1::/48,2001:db8:2::/64"
ENV IPV6AUTOPTR_PTR_CONFIG_FILE="ipv6autoptr.conf"
ENV IPV6AUTOPTR_USE_CUSTOM_PTR=true
ENV IPV6AUTOPTR_LOG_LEVEL="INFO"

# Expose the DNS port
EXPOSE 53/udp 53/tcp

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD dig @localhost -p $IPV6AUTOPTR_PORT -x 2001:db8:1::1 || exit 1

# Default command
CMD ["python", "ipv6autoptr.py", "--config", "config.yaml"]