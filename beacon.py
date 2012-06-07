# -*- coding: utf-8 -*-
"""
Location is performed by UDB broadcasts.
@license: MIT License
"""

import socket
import errno
import select
import threading
import uuid

try:
    import netifaces
    HAS_NETIFACES = True
except ImportError:
    HAS_NETIFACES = False

###########################################################################
###########################################################################

CLIENT_TIMEOUT = 2
SERVER_TIMEOUT = 0.2
MAX_INTERFACE_SERVERS = 5  #: maximum count of beacons on a single interface
UUID_LENGTH = 16

###########################################################################
###########################################################################

def get_broadcast_addresses():
    """
    Retrieve broadcast addresses from network interfaces.
    """
    addr_list = []
    if HAS_NETIFACES:
        for iface in netifaces.interfaces():
            addresses = netifaces.ifaddresses(iface).get(netifaces.AF_INET)
            if addresses is None:
                continue
            for address in addresses:
                broadcast_addr = address.get("broadcast")
                if broadcast_addr is None:
                    continue
                addr_list.append(broadcast_addr)
    return ["127.0.0.1", "255.255.255.255", "<broadcast>"] + addr_list

###################################################################

def _find_servers(port, key, wait_for_all):
    """
    @return: list of resolved address
    """
    addresses = get_broadcast_addresses()

    bcast_socks = []
    for bcast_addr in addresses:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.sendto(key, (bcast_addr, port))
            bcast_socks.append(sock)
        except socket.error, err:
            if err.errno != errno.ENETUNREACH:
                raise
    
    servers = []
    srv_uuids = set()
    max_tries = len(bcast_socks) * MAX_INTERFACE_SERVERS
    while max_tries > 0:
        try:
            rlist, dummy_wlist, dummy_xlist = select.select(bcast_socks, [], [],
                                                            CLIENT_TIMEOUT)
        except socket.error:
            break
        if len(rlist) == 0:
            # timeout, no respond
            break

        max_tries -= len(rlist)

        try:
            for bcast_sock in rlist:
                message, (ip, dummy_port) = bcast_sock.recvfrom(UUID_LENGTH + len(key))
                if len(message) < UUID_LENGTH:
                    continue
                srv_uuid = message[:UUID_LENGTH]
                srv_key = message[UUID_LENGTH:]
                if (srv_key == key) and (srv_uuid not in srv_uuids):
                    servers.append(ip)
                    srv_uuids.add(srv_uuid)
                    if not wait_for_all:
                        max_tries = 0
                        break
        except socket.error, e:
            continue

    return servers

###################################################################

def find_all_servers(port, key):
    return _find_servers(port, key, True)

###################################################################

def find_server(port, key):
    """
    Find first responding server.
    @return: IP address or None if not found.
    """
    servers = _find_servers(port, key, False)
    if len(servers) == 0:
        return None
    else:
        return servers[0]

###########################################################################
###########################################################################

class Beacon(threading.Thread):
    def __init__(self, port, key):
        threading.Thread.__init__(self)
        self.port = port
        self.key = key
        self.quit = False
        self.unique_id = uuid.uuid1().bytes

    ################################################

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(SERVER_TIMEOUT)
        sock.bind(("", self.port))

        while not self.quit:
            try:
                message, address = sock.recvfrom(len(self.key))
            except socket.error as exc:
                continue

            if message != self.key:
                # not my client
                continue

            sock.sendto(self.unique_id + self.key, address)

        sock.close()
