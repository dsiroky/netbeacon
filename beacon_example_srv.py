#!/usr/bin/python

import time

import beacon

b = beacon.Beacon(12000, "abc")
b.daemon = True
b.start()

time.sleep(10000)
