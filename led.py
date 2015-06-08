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
# simple routines to output a 4 char string to our LED
#

import spidev
import time
import datetime

# ASCII subset encoded for 7 segment display output:
ASCII_OFFSET = 32
ASCII_MAX    = 32 + 64

code_table = [
  #        !     "     #     $     %     &     '     (     )    *     +     ,     -     .     /
  0x00, 0x00, 0x22, 0x00, 0x00, 0x00, 0x00, 0x20, 0x39, 0x0f, 0x00, 0x00, 0x10, 0x40, 0x10, 0x00,
  #  0     1     2     3     4     5     6     7     8     9    :     ;     <     =     >     ?     
  0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00,
  #  @     A     B     C     D     E     F     G     H     I     J     K     L     M     N     O
  0x00, 0x77, 0x7c, 0x39, 0x5e, 0x79, 0x71, 0x7d, 0x76, 0x06, 0x0e, 0x70, 0x38, 0x37, 0x37, 0x3f,
  #  P     Q     R     S     T     U     V     W     X     Y     Z     [     \     ]     ^     _ 
  0x73, 0x3f, 0x50, 0x6d, 0x78, 0x3e, 0x3e, 0x3e, 0x49, 0x72, 0x52, 0x39, 0x64, 0x0f, 0x23, 0x08
]

#
# pretty slow settings because of our SPI long cable
#

SPEED_HZ      = 7629
DELAY_USEC    = 10
BITS_PER_WORD = 8 

def spi_sendrecv (byte):

    resp = spi.xfer([byte], SPEED_HZ, DELAY_USEC, BITS_PER_WORD)
    #print "%d -> %d" % (byte, resp[0])


def led_write (s):

    #
    # flush state
    #

    for i in range(4):
        spi_sendrecv(0)
     
    # header
    spi_sendrecv(42) 

    for i in range(4):

        code = code_table[ord(s[i])-ASCII_OFFSET]

        spi_sendrecv(code)

spi = spidev.SpiDev()

spi.open(0,0)

if __name__ == "__main__":

    while True:
        led_write ('HAL ')
        time.sleep(1)
        led_write ('9000')
        time.sleep(1)

        dt = datetime.datetime.now()

        led_write (dt.strftime("%H%M"))
        time.sleep(1)


