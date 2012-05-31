# -*- coding: utf-8 -*-
"""
Location is performed by UDB broadcasts.
@license: MIT License
"""

import socket
import threading

try:
    import netifaces
    HAS_NETIFACES = True
except ImportError:
    HAS_NETIFACES = False

###########################################################################
###########################################################################

CLIENT_TIMEOUT = 2
SERVER_TIMEOUT = 0.2

###########################################################################
###########################################################################

def get_broadcast_addresses():
    """
    Retrieve broadcast addresses from network interfaces.
    """
    addr_list = []
    for iface in netifaces.interfaces():
        addresses = netifaces.ifaddresses(iface).get(netifaces.AF_INET)
        if addresses is None:
            continue
        for address in addresses:
            broadcast_addr = address.get("broadcast")
            if broadcast_addr is None:
                continue
            addr_list.append(broadcast_addr)
    return addr_list

###################################################################

def _find_server(signal, bcast_addr, port, key, result_idx, results):
    """
    stores to results (received data, address) or (None, None)
    """
    bcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    bcast_sock.settimeout(CLIENT_TIMEOUT)
    try:
        bcast_sock.sendto(key, (bcast_addr, port))
        results[result_idx] = bcast_sock.recvfrom(len(key))
        signal.set()
    except (socket.timeout, socket.error):
        results[result_idx] = (None, None)

###################################################################

def find_server(port, key):
    """
    @return: IP address or None if not found.
    """
    # generic broadcast addresses
    addresses = ["127.0.0.1", "255.255.255.255", "<broadcast>"]
    if HAS_NETIFACES:
        # broadcast addresses by interfaces
        addresses += get_broadcast_addresses()

    results = [(None, None)] * len(addresses)
    threads = []
    signal = threading.Event()

    # perform parallel lookup on multiple addresses
    for i, broadcast_addr in enumerate(addresses):
        thr = threading.Thread(target=_find_server, name="find_server_%i" % i,
                            args=(signal, broadcast_addr, port, key, i, results))
        threads.append(thr)
        thr.start()

    # wait for the first thread that discovers the server
    signal.wait(CLIENT_TIMEOUT)

    # find correct result
    for i, (rkey, addr) in enumerate(results):
        if rkey == key:
            return addr[0]  # IP part
            # leave the rest of threads to rott

    # no response or mole is among us (bad key)
    return None

###########################################################################
###########################################################################

class Beacon(threading.Thread):
    def __init__(self, port, key):
        threading.Thread.__init__(self)
        self.port = port
        self.key = key
        self.quit = False

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

            sock.sendto(self.key, address)

        sock.close()
