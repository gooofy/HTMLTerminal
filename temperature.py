#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2015 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re, os

# function: read and parse sensor data file
def read_sensor(path):
    value = -100.0
    try:
        f = open(path, "r")
        line = f.readline()
        if re.match(r"([0-9a-f]{2} ){9}: crc=[0-9a-f]{2} YES", line):
            line = f.readline()
            m = re.match(r"([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
            if m:
                value = float(m.group(2)) / 1000.0
        f.close()
    except (IOError), e:
        print "Error reading", path, ": ", e
    return value

def measure_temperatures (term_location, sensor_path_inside, sensor_path_outside):

    temp_inside = read_sensor (sensor_path_inside)
    temp_outside = read_sensor (sensor_path_outside)

    return (term_location, temp_inside, temp_outside)

