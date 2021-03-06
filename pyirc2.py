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
# Infrared decoder for 
#
# - RUWIDO Merlin IR Keyboard protocol
#   56kHz receiver required! (e.g. TSOP 31256)
#
# RUWIDO (SIEMENS) protocol
#
#   SIEMENS frame:  1 start bit + 22 data bits + no stop bit
#   SIEMENS data:   13 address bits + 1 repeat bit + 7 data bits + 1 unknown bit
#
#   start  bit           data "0":            data "1":
#   -------_______       _______-------       -------_______
#    250us  250us         250us  250us         250us  250us


VERBOSE = False

STATE_IDLE      = 2
STATE_DATA      = 1
STATE_GAP       = 3

MAX_PULSE_LEN   = 600
SHORT_PULSE_LEN = 250

GAP_LEN         = 50000

LIRC_DEVICE='/dev/lirc0'

state = STATE_IDLE

codes = {
    'KEY_ENTER': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 150 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 150 , 400 , 400 ,
    200 , 200 , 400 , 400 , 400 , 350 ,
    200 , 200 , 200 , 200 , 400 ],

    'KEY_SPACE': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 400 , 400 , 200 ,
    200 , 400 , 200 , 200 , 400 ],

    'KEY_Q': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 200 , 200 , 400 ],

    'KEY_W': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 400 , 400 , 400 , 400 ],

    'KEY_E': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 , 400 , 200 , 200 , 200 , 200 ,
    400 ],

    'KEY_R': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 400 , 400 , 200 ],

    'KEY_T': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 200 , 200 , 200 , 200 , 400 ,
    200 ],

    'KEY_Y': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 200 , 200 , 400 , 200 , 200 ,
    400 ],

    'KEY_U': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 400 , 200 , 200 , 200 , 200 ,
    400 ],

    'KEY_I': [ 250 , 350 , 200 , 200 , 200 , 150 ,
    200 , 200 , 200 , 200 , 200 , 150 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 150 , 200 , 200 , 200 , 150 ,
    400 , 200 , 200 , 400 , 200 , 200 ,
    400 ],

    'KEY_O': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 150 , 200 , 200 ,
    200 , 150 , 200 , 150 , 400 , 400 ,
    200 , 150 , 200 , 200 , 400 , 350 ,
    200 , 200 , 400 , 400 , 400 ],

    'KEY_P': [ 250 , 350 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 200 ,
    200 , 150 , 200 , 150 , 400 , 400 ,
    200 , 150 , 200 , 150 , 400 , 400 ,
    200 , 150 , 400 , 150 , 200 , 350 ,
    200 ],

    'KEY_A': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 400 , 400 , 200 , 200 ,
    400 ],

    'KEY_S': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 200 , 200 , 400 , 400 ],

    'KEY_D': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 400 , 200 , 200 , 200 ,
    200 , 400 , 200 ],

    'KEY_F': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 , 400 , 200 , 200 , 400 , 400 ,
    200 ],

    'KEY_G': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 , 400 , 400 , 400 , 400 ],

    'KEY_H': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 , 400 , 400 , 200 , 200 , 400 ,
    200 ],

    'KEY_J': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 , 200 , 200 , 400 , 400 , 400 ,
    200 ],

    'KEY_K': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 , 200 , 200 , 200 , 200 , 400 ,
    400 ],

    'KEY_L': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 , 200 , 200 , 200 , 200 , 200 ,
    200 , 400 , 200 ],

    'KEY_Z': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 200 , 200 , 400 , 400 , 400 ,
    200 ],

    'KEY_X': [ 250 , 350 , 200 , 200 , 200 , 150 ,
    200 , 150 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 150 ,
    200 , 400 , 400 , 150 , 200 , 400 ,
    200 ],

    'KEY_C': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 400 , 200 , 200 , 400 ,
    400 ],

    'KEY_V': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 400 , 200 , 200 , 400 , 400 ,
    200 ],

    'KEY_B': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 400 , 400 , 400 , 400 ,
    200 ],

    'KEY_N': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 ],

    'KEY_M': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 ],

    'KEY_POWER': [ 200 , 400 , 200 , 150 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 150 , 400 , 400 ,
    200 , 200 , 400 , 400 , 400 , 350 ,
    200 , 200 , 400 , 400 , 200 ],

    'KEY_EXIT': [ 200 , 400 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 400 ,
    400 , 400 , 400 , 400 , 400 , 400 ,
    400 , 400 , 200 ],

    'KEY_1': [ 250 , 400 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 350 ,
    200 , 150 , 200 , 150 , 400 , 150 ,
    200 , 150 , 200 , 150 , 200 , 400 ,
    400 ],

    'KEY_2': [ 250 , 350 , 200 , 150 , 200 , 150 ,
    200 , 150 , 250 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 350 ,
    200 , 150 , 200 , 150 , 400 , 150 ,
    200 , 150 , 250 , 150 , 200 , 150 ,
    200 , 350 , 200 ],

    'KEY_3': [ 250 , 350 , 200 , 150 , 200 , 150 ,
    200 , 150 , 250 , 150 , 200 , 150 ,
    200 , 150 , 250 , 150 , 400 , 350 ,
    200 , 150 , 400 , 400 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    400 ],

    'KEY_4': [ 250 , 350 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 450 , 350 ,
    200 , 150 , 400 , 350 , 200 , 150 ,
    200 , 150 , 250 , 150 , 400 , 400 ,
    200 ],

    'KEY_5': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 400 , 200 , 200 ,
    200 , 200 , 400 , 400 , 400 ],

    'KEY_6': [ 250 , 350 , 200 , 200 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 350 ,
    200 , 200 , 400 , 350 , 200 , 200 ,
    200 , 150 , 400 , 150 , 200 , 400 ,
    200 ],

    'KEY_7': [ 250 , 350 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 350 ,
    200 , 150 , 400 , 350 , 200 , 150 ,
    400 , 350 , 200 , 150 , 400 ],

    'KEY_8': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 400 , 200 , 200 ,
    400 , 400 , 400 , 400 , 200 ],

    'KEY_9': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 400 , 200 , 200 ,
    400 , 200 , 200 , 400 , 400 ],

    'KEY_0': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 400 , 200 , 200 ,
    400 , 200 , 200 , 200 , 200 , 400 ,
    200 ],

    'KEY_PLAY': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 400 ,
    400 ],

    'KEY_REWIND': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 200 , 200 , 200 ,
    200 , 200 , 200 , 400 , 400 , 400 ,
    200 ],

    'KEY_FORWARD': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 400 , 200 ],

    'KEY_HELP': [ 250 , 350 , 200 , 150 , 250 , 150 ,
    200 , 150 , 200 , 150 , 250 , 150 ,
    200 , 150 , 250 , 150 , 450 , 350 ,
    400 , 400 , 450 , 350 , 400 , 150 ,
    200 , 350 , 450 ],

    'KEY_RECORD': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 200 , 200 , 350 , 200 , 200 ,
    400 , 400 , 200 , 150 , 400] ,

    'KEY_STOP': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 ],

    'KEY_RADIO': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 400 , 400 , 400 , 200 ,
    200 , 200 , 200 , 400 , 200 ],

    'KEY_UP': [ 200 , 350 , 200 , 200 , 200 , 150 ,
    250 , 150 , 200 , 150 , 200 , 200 ,
    200 , 200 , 200 , 150 , 450 , 350 ,
    400 , 400 , 450 , 350 , 200 , 150 ,
    400 , 400 , 400 ],

    'KEY_DOWN': [ 250 , 400 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 400 ,
    400 , 350 , 400 , 350 , 200 , 150 ,
    200 , 150 , 400 , 350 , 200 ],

    'KEY_LEFT': [ 200 , 400 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 350 ,
    400 , 400 , 400 , 400 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 ],

    'KEY_RIGHT': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 200 , 200 , 400 , 200 ,
    200 , 200 , 200 , 200 , 200 , 400 ,
    200 ],

    'KEY_OK': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 400 , 200 , 200 , 400 ,
    200 , 200 , 200 , 200 , 400 ],

    'KEY_VOLUMEUP': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 ],

    'KEY_VOLUMEDOWN': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 400 , 400 , 400 ],

    'KEY_CHANNELUP': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 400 , 200 , 200 , 400 ,
    200 ],

    'KEY_CHANNELDOWN': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 200 , 200 , 200 , 200 ,
    400 , 400 , 200 , 200 , 400 ],

    'KEY_TEXT': [ 250 , 350 , 200 , 200 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 200 ,
    200 , 200 , 200 , 150 , 400 , 350 ,
    400 , 350 , 400 , 400 , 400 , 400 ,
    200 , 150 , 400 ],

    'KEY_RED': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 400 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 400 ,
    200 ],

    'KEY_GREEN': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 200 , 200 , 400 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    400 ],

    'KEY_YELLOW': [ 250 , 350 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 200 ,
    200 , 150 , 200 , 200 , 400 , 400 ,
    400 , 150 , 200 , 400 , 200 , 150 ,
    200 , 150 , 200 , 200 , 400 , 400 ,
    200 ],

    'KEY_BLUE': [ 200 , 400 , 200 , 150 , 200 , 150 ,
    250 , 150 , 200 , 150 , 200 , 200 ,
    200 , 150 , 200 , 150 , 450 , 350 ,
    400 , 150 , 250 , 350 , 250 , 150 ,
    200 , 150 , 450 , 350 , 400 ],

    'KEY_MENU': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 200 , 200 , 200 ,
    200 , 400 , 400 , 200 , 200 , 400 ,
    200 ],

    'KEY_MENU_P': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 400 , 200 , 200 , 200 ,
    200 , 400 , 200 , 200 , 400 ],

    'KEY_MENU_M': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 400 , 200 , 200 , 200 ,
    200 , 400 , 400 , 400 , 150 ],

    'KEY_MENU_S': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 , 400 , 400 , 200 , 200 , 400 ,
    400 , 200 , 200 , 400 , 200 ],

    'KEY_TAB': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 400 , 400 , 400 ,
    400 , 200 , 200 , 400 , 200 ],

    'KEY_CTRL': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 200 , 200 , 200 , 200 , 400 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 400 ],

    'KEY_LEFTALT': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 200 , 200 , 200 , 200 , 400 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    400 ],

    'KEY_RIGHTALT': [ 250 , 350 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 200 ,
    200 , 200 , 200 , 200 , 200 , 400 ,
    200 , 200 , 400 , 200 , 200 , 400 ,
    400 ],

    'KEY_LEFTSHIFT': [ 200 , 400 , 200 , 200 , 200 , 150 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 150 , 200 , 150 , 400 , 200 ,
    200 , 150 , 200 , 200 , 200 , 400 ,
    200 , 200 , 200 , 200 , 200 , 150 ,
    400 , 400 , 200 ],

    'KEY_BACKSPACE': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 400 , 400 , 400 ,
    400 , 400 , 400 ],

    'KEY_APOSTROPHE': [ 250 , 350 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 200 , 150 ,
    200 , 150 , 200 , 150 , 400 , 350 ,
    200 , 150 , 400 , 150 , 200 , 400 ,
    400 , 400 , 200 , 150 , 400 ],

    'KEY_SLASH': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 200 , 200 , 200 ,
    200 , 400 , 200 , 200 , 200 , 200 ,
    400 ],

    'KEY_COMMA': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 400 , 400 ,
    200 , 200 , 400 , 200 , 200 , 400 ,
    400 , 200 , 200 , 400 , 400 ],

    'KEY_DOT': [ 200 , 400 , 200 , 200 , 200 , 200 ,
    200 , 200 , 200 , 200 , 200 , 150 ,
    200 , 200 , 200 , 150 , 400 , 350 ,
    200 , 200 , 400 , 200 , 200 , 400 ,
    400 , 200 , 200 , 200 , 200 , 400 ,
    200 ],

    'KEY_EQUAL': [ 150 , 400 , 200 , 200 , 200 , 200 ,
        150 , 200 , 200 , 200 , 200 , 200 ,
        200 , 200 , 200 , 200 , 400 , 400 ,
        200 , 200 , 400 , 450 , 350 , 200 ,
        200 , 200 , 200 , 400 , 400 ],

    'KEY_SEMICOLON': [ 200 , 400 , 200 , 150 , 200 , 200 ,
        200 , 200 , 200 , 200 , 200 , 200 ,
        200 , 200 , 200 , 200 , 400 , 350 ,
        200 , 200 , 400 , 150 , 200 , 400 ,
        200 , 200 , 400 , 150 , 200 , 400 ,
        200 ] 
    }


def decode_data(data):

    for k in codes:

        code = codes[k]

        l = len(code)
        if l != len(data):
            continue

        matched = True

        for i in range(l):
            diff = float(abs (code[i] - data[i])) / float(code[i])
            if diff > 0.4:
                matched = False
                break

        if matched:
            if VERBOSE:
                print "MATCH! %s data: %d, code: %d" % (k, len(data), len(code))
                print "data: ",
                for i in range(l):
                    print "%4d" % data[i],
                print
                print "code: ",
                for i in range(l):
                    print "%4d" % code[i],
                print
                print "match ",
                for i in range(l):
                    diff = float(abs (code[i] - data[i])) / float(code[i])
                    print "%4.2f" % diff,
                print
            return k

    return None

def pyirc_nextcode():

    global state

    code = None
    data = []

    with open(LIRC_DEVICE, 'rb') as f:

        while True:

            length = 0

            length  = ord(f.read(1))
            length |= ord(f.read(1)) << 8
            length |= ord(f.read(1)) << 16
            ctrl    = ord(f.read(1))
     
            if length > MAX_PULSE_LEN:

                if state == STATE_GAP:
                    if length < GAP_LEN:
                        continue
                elif state == STATE_DATA:
                    state = STATE_GAP

                    code = decode_data(data)

                    if VERBOSE:
                        print "GAP"

                    if code is not None:
                        break

                    continue 

                if VERBOSE:
                    print "IDLE"
                state = STATE_IDLE
                data  = 0
                nbits = 0
                continue

            if state == STATE_GAP:
                continue

            if state == STATE_IDLE:
                data  = [ length ]
                state = STATE_DATA

            elif state == STATE_DATA:

                data.append(length)

            if VERBOSE:
                print "%d: %8d state=%d %s" % (ctrl, length, state, repr(data))


    return code


if __name__ == "__main__":


    while True:

        code = pyirc_nextcode()

        print code



