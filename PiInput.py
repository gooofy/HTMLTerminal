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

#
# IR based Input events for RaspberryPi
#

import time
from pyirc2 import pyirc_nextcode

REPEAT_DELAY = 500

class PiInput(object):

    def __init__(self, name='PiInput'):
        self.lastkey = ''
        self.lasttime = 0


    def process_events (self):

        # Read next code
        key = pyirc_nextcode()

        #print "Got key: %s" % key

        if key is not None:

            t = int(time.time() * 1000) 
            d = t - self.lasttime

            if key != self.lastkey or d > REPEAT_DELAY:

                self.lastkey  = key
                self.lasttime = t
           
                return key
 
            #else:
            #    print "     ==== REPEAT IGNORED ===="

        return None


if __name__ == "__main__":

    inp = PiInput()

    while True:

        inp.next_event()

        #time.sleep(1)


