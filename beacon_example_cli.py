#!/usr/bin/python

import beacon

print("single: %r" % beacon.find_server(12000, b"abc"))
print("all: %r" % beacon.find_all_servers(12000, b"abc"))
