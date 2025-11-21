#!/usr/bin/env python3
"""
LICENSE http://www.apache.org/licenses/LICENSE-2.0


Copyright 2023 Dmitriy Terehin https://github.com/meatlayer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”),
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import argparse
import datetime
import sys
import time
import threading
import traceback
import ipaddress
import socketserver
import concurrent.futures
import struct
import logging
import os
import yaml
try:
    from dnslib import *
except ImportError:
    print("Missing dependency dnslib: <https://pypi.python.org/pypi/dnslib>. Please install it with `pip`.")
    sys.exit(2)

class DomainName(str):
    def __getattr__(self, item):
        return DomainName(item + '.' + self)


class Config:
    """Configuration management class that handles loading from multiple sources:
    Priority order: CLI args > Environment variables > Config file > Defaults
    """

    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.config = {}

        # Default configuration values
        self.defaults = {
            'server': {
                'port': 5353,
                'bind_address': '::',
                'enable_tcp': False,
                'enable_udp': True,
                'verbose': 0
            },
            'dns': {
                'ttl': 86400,
                'domain_suffix': 'ip6.example.com.',
                'max_workers': 32
            },
            'ipv6': {
                'subnets': ['2001:db8:1::/48', '2001:db8:2::/64']
            },
            'ptr_records': {
                'config_file': 'ipv6autoptr.conf',
                'use_custom': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'file': None
            }
        }

        self._load_config()

    def _load_config(self):
        """Load configuration from file, then apply environment overrides"""
        # Start with defaults
        self.config = self._deep_copy(self.defaults)

        # Load from YAML file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                self._merge_config(self.config, file_config)
            except Exception as e:
                print(f"Warning: Failed to load config file {self.config_file}: {e}")

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _deep_copy(self, d):
        """Simple deep copy for nested dictionaries"""
        if isinstance(d, dict):
            return {k: self._deep_copy(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self._deep_copy(v) for v in d]
        else:
            return d

    def _merge_config(self, base, override):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self):
        """Apply environment variable overrides with IPV6AUTOPTR_ prefix"""
        env_mappings = {
            'IPV6AUTOPTR_PORT': ('server', 'port', int),
            'IPV6AUTOPTR_BIND_ADDRESS': ('server', 'bind_address', str),
            'IPV6AUTOPTR_ENABLE_TCP': ('server', 'enable_tcp', self._str_to_bool),
            'IPV6AUTOPTR_ENABLE_UDP': ('server', 'enable_udp', self._str_to_bool),
            'IPV6AUTOPTR_VERBOSE': ('server', 'verbose', int),
            'IPV6AUTOPTR_TTL': ('dns', 'ttl', int),
            'IPV6AUTOPTR_DOMAIN_SUFFIX': ('dns', 'domain_suffix', str),
            'IPV6AUTOPTR_MAX_WORKERS': ('dns', 'max_workers', int),
            'IPV6AUTOPTR_SUBNETS': ('ipv6', 'subnets', self._parse_comma_list),
            'IPV6AUTOPTR_PTR_CONFIG_FILE': ('ptr_records', 'config_file', str),
            'IPV6AUTOPTR_USE_CUSTOM_PTR': ('ptr_records', 'use_custom', self._str_to_bool),
            'IPV6AUTOPTR_LOG_LEVEL': ('logging', 'level', str),
            'IPV6AUTOPTR_LOG_FORMAT': ('logging', 'format', str),
            'IPV6AUTOPTR_LOG_FILE': ('logging', 'file', str)
        }

        for env_var, (section, key, converter) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    self.config[section][key] = converter(value)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {env_var}: {value} ({e})")

    def _str_to_bool(self, value):
        """Convert string to boolean"""
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', 'yes', '1', 'on', 'enable')

    def _parse_comma_list(self, value):
        """Parse comma-separated list"""
        if isinstance(value, list):
            return value
        return [item.strip() for item in str(value).split(',') if item.strip()]

    def get(self, *path):
        """Get configuration value using dot notation (e.g., get('server', 'port'))"""
        current = self.config
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def set_from_args(self, args):
        """Update configuration with command line arguments (highest priority)"""
        if hasattr(args, 'port') and args.port is not None:
            self.config['server']['port'] = args.port
        if hasattr(args, 'tcp') and args.tcp:
            self.config['server']['enable_tcp'] = True
        if hasattr(args, 'udp') and args.udp:
            self.config['server']['enable_udp'] = True
        if hasattr(args, 'verbose') and args.verbose is not None:
            self.config['server']['verbose'] = args.verbose
        if hasattr(args, 'config') and args.config:
            # If a different config file is specified via CLI, reload everything
            self.config_file = args.config
            self._load_config()

    @property
    def port(self):
        return self.get('server', 'port')

    @property
    def bind_address(self):
        return self.get('server', 'bind_address')

    @property
    def enable_tcp(self):
        return self.get('server', 'enable_tcp')

    @property
    def enable_udp(self):
        return self.get('server', 'enable_udp')

    @property
    def verbose(self):
        return self.get('server', 'verbose')

    @property
    def ttl(self):
        return self.get('dns', 'ttl')

    @property
    def domain_suffix(self):
        return self.get('dns', 'domain_suffix')

    @property
    def max_workers(self):
        return self.get('dns', 'max_workers')

    @property
    def subnets(self):
        return self.get('ipv6', 'subnets')

    @property
    def ptr_config_file(self):
        return self.get('ptr_records', 'config_file')

    @property
    def use_custom_ptr(self):
        return self.get('ptr_records', 'use_custom')


IPV6AUTOPTR_VERSION = "0.1"

# Global configuration object - will be initialized in main()
config = None
#IP = '122.123.124.125'
#IP6 = '2a0a:XXXX:0:a000::125'

#TTL = 60 * 5

#soa_record = SOA(
#    mname=D.ns1,  # primary name server
#    rname=D.robot,  # email of the domain administrator
#    times=(
#        2023120829,  # serial number
#        60 * 60 * 1,  # refresh
#        60 * 60 * 3,  # retry
#        60 * 60 * 24,  # expire
#        60 * 60 * 1,  # minimum
#    )
#)
#ns_records = [NS(D.ns1), NS(D.ns2)]
#records = {
#    D: [A(IP), AAAA(IP6), MX(D.mail), soa_record] + ns_records,
#    D.ns1: [A(IP)],  # MX and NS records must never point to a CNAME alias (RFC 2181 section 10.3)
#    D.ns2: [A(IP)],
#    D.mail: [A(IP)],
#    D.robot: [CNAME(D)],
#}

# func for ipv6 auto ptr
def dns_response_ipv6ptr(data):
    request = DNSRecord.parse(data)
    reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)
    qname = request.q.qname
    qn = str(qname)
    qtype = request.q.qtype
    qt = QTYPE[qtype]

    ptrdomain_name = str(request.q.qname).rstrip('.ip6.arpa.')[::-1]
    ptrdomain_name = ptrdomain_name.replace('.', '')
    ipv6_domain = DomainName(config.domain_suffix)

    #if req type = PTR
    if '.ip6.arpa' in qn:
        #print("OK ip6.arpa found")

        if request.q.qtype == '12' or request.q.qtype == QTYPE.PTR or request.q.qtype == 'PTR':

            # IPv6 PTR record name
            ptr_name = str(request.q.qname).rstrip('.ip6.arpa.')[::-1]

            # Split the PTR record name into its individual segments
            segments = ptr_name.split(".")

            # Convert the hexadecimal segments to bytes and join them together
            hex_string = "".join(segments[::1])
            byte_string = bytes.fromhex(hex_string)

            # Create an IPv6 address object from the byte string
            ipv6_addr = ipaddress.IPv6Address(byte_string)

            logging.info("CLIENT REQUEST: " + qn)

            # Search the subnets for a match
            match = False
            for subnet_str in config.subnets:
                subnet = ipaddress.IPv6Network(subnet_str)
                if ipv6_addr in subnet:
                    match = True
                         
                    # read config file to retrieve parameter-value pairs for PTR answer
                    with open(config.ptr_config_file) as f:
                        lines = f.readlines()
                        # parse parameters from config file
                        config_params = {}
                        for line in lines:
                            line = line.strip()
                            # Skip empty lines and comments
                            if not line or line.startswith('#'):
                                continue
                            if ' = ' in line:
                                param, value = line.split(' = ', 1)
                                config_params[param.strip()] = value.strip()

                    # Check if the PTR domain name matches a config parameter and replace it with the corresponding value
                    for param, value in config_params.items():
                        if qn in param:
                            ptr_answerd = value
                            break
                        else:
                            ptr_answerd = str(ptrdomain_name+'.'+ipv6_domain)
                    
                    logging.info(f"IPV6: {ipv6_addr} found in subnet {subnet} and resolv answer as: {ptr_answerd}")
                    logging.info("SERVER ANSWER: " + ptr_answerd)
                    reply.add_answer(RR(rname=qname, rtype=QTYPE.PTR, rdata=PTR(ptr_answerd), ttl=config.ttl))
                    break

            else:
                # If IPV6 found in subnets, return Non-existent Internet Domain Names Definition
                logging.info(f"{ipv6_addr} is not in any of the subnets")
                reply.header.rcode = RCODE.NXDOMAIN

    else:
        # Query not ip6.arpa, return Non-existent Internet Domain Names Definition
        reply.header.rcode = RCODE.NXDOMAIN

    return reply.pack()

class BaseRequestHandler(socketserver.BaseRequestHandler):

    executor = None  # Will be initialized when config is available

    def get_data(self):
        raise NotImplementedError

    def send_data(self, data):
        raise NotImplementedError

    def handle(self):
        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        logging.info("%s request %s (%s %s):" % (self.__class__.__name__[:3], now, self.client_address[0], self.client_address[1]))

        data = self.get_data()
        future = self.executor.submit(dns_response_ipv6ptr, data)

        def send_response():
            try:
                response = future.result()
                self.send_data(response)
            except Exception as e:
                traceback.print_exc(file=sys.stderr)

        threading.Thread(target=send_response).start()


class TCPRequestHandler(BaseRequestHandler):

    def get_data(self):
        data = self.request.recv(8192)
        sz = struct.unpack('>H', data[:2])[0]
        if sz < len(data) - 2:
            raise Exception("Wrong size of TCP packet")
        elif sz > len(data) - 2:
            raise Exception("Too big TCP packet")
        return data[2:]

    def send_data(self, data):
        try:
            sz = struct.pack('!H', len(data))
            if self.request.fileno() == -1:
                return
            self.request.sendall(sz + data)
        except OSError as e:
            if e.errno == 9:
                logging.error("Socket closed")
            else:
                logging.error("Error sending data: {}".format(str(e)))


class UDPRequestHandler(BaseRequestHandler):

    def get_data(self):
        return self.request[0]

    def send_data(self, data):
        try:
            return self.request[1].sendto(data, self.client_address)
        except OSError as e:
            logging.exception(f"Error while sending data: {e}")

def main():
    global config

    parser = argparse.ArgumentParser(description='Start a IPV6AUTOPTR implemented in Python.')
    parser.add_argument('--port', default=None, type=int, help='The port to listen on.')
    parser.add_argument('--tcp', action='store_true', help='Listen to TCP connections.')
    parser.add_argument('--udp', action='store_true', help='Listen to UDP datagrams.')
    parser.add_argument("--verbose", action = "count", default=None, help="Increase verbosity")
    parser.add_argument('--config', default='config.yaml', help='Configuration file path.')
    args = parser.parse_args()

    # Initialize configuration system
    config = Config(args.config)
    config.set_from_args(args)

    # If no protocol specified via CLI, use config defaults
    if not (args.udp or args.tcp):
        if not (config.enable_udp or config.enable_tcp):
            parser.error("Please select at least one of --udp or --tcp, or enable them in config.")

    print("Starting ...")

    servers = []
    # Use CLI args if specified, otherwise use config defaults
    enable_udp = args.udp or config.enable_udp
    enable_tcp = args.tcp or config.enable_tcp

    if enable_udp:
        servers.append(socketserver.ThreadingUDPServer((config.bind_address, config.port), UDPRequestHandler))
    if enable_tcp:
        servers.append(socketserver.ThreadingTCPServer((config.bind_address, config.port), TCPRequestHandler))

    # Set up logging based on verbose level
    verbose_level = config.verbose
    if verbose_level == 1:
        level = logging.INFO
    elif verbose_level >= 2:
        level = logging.DEBUG
    else:
        level = logging.WARN

    # Configure logging from config
    log_config = {
        'format': config.get('logging', 'format'),
        'level': level,
    }
    if config.get('logging', 'file'):
        log_config['filename'] = config.get('logging', 'file')

    logging.basicConfig(**log_config)

    # Initialize the thread pool executor with configured max workers
    BaseRequestHandler.executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers)

    for s in servers:
        thread = threading.Thread(target=s.serve_forever)  # that thread will start one more thread for each request
        thread.daemon = True  # exit the server thread when the main thread terminates
        thread.start()
        print("%s server loop running in thread: %s" % (s.RequestHandlerClass.__name__[:3], thread.name))

    try:
        while 1:
            time.sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        for s in servers:
            s.shutdown()

if __name__ == '__main__':

    header  = r"     ___ ______     ____     _   _   _ _____ ___  ____ _____ ____  " + "\n"
    header += r"    |_ _|  _ \ \   / / /_   / \ | | | |_   _/ _ \|  _ \_   _|  _ \  " + "\n"
    header += r"     | || |_) \ \ / / '_ \ / _ \| | | | | || | | | |_) || | | |_) | " + "\n"
    header += r"     | ||  __/ \ V /| (_) / ___ \ |_| | | || |_| |  __/ | | |  _ < " + "\n"
    header += r"    |___|_|     \_/  \___/_/   \_\___/  |_| \___/|_|    |_| |_| \_\ " + "\n"
    header += "     powered by Dmitriy Terehin | https://github.com/meatlayer | v %s  \n" %IPV6AUTOPTR_VERSION

    print(header)
    main()
