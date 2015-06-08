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
# X11 input handler
#

import ctypes
import time
import math
import os
import platform
import datetime
from base64 import b64decode

from egl import xlib_wrapper

keymap = {
       36 : 'KEY_ENTER',
       65 : 'KEY_SPACE',
       24 : 'KEY_Q',
       25 : 'KEY_W',
       26 : 'KEY_E',
       27 : 'KEY_R',
       28 : 'KEY_T',
       29 : 'KEY_Y',
       30 : 'KEY_U',
       31 : 'KEY_I',
       32 : 'KEY_O',
       33 : 'KEY_P',
       38 : 'KEY_A',
       39 : 'KEY_S',
       40 : 'KEY_D',
       41 : 'KEY_F',
       42 : 'KEY_G',
       43 : 'KEY_H',
       44 : 'KEY_J',
       45 : 'KEY_K',
       46 : 'KEY_L',
       52 : 'KEY_Z',
       53 : 'KEY_X',
       54 : 'KEY_C',
       55 : 'KEY_V',
       56 : 'KEY_B',
       57 : 'KEY_N',
       58 : 'KEY_M',
       78 : 'KEY_POWER', # Scroll Lock
        9 : 'KEY_EXIT',  # Esc
       10 : 'KEY_1',
       11 : 'KEY_2',
       12 : 'KEY_3',
       13 : 'KEY_4',
       14 : 'KEY_5',
       15 : 'KEY_6',
       16 : 'KEY_7',
       17 : 'KEY_8',
       18 : 'KEY_9',
       19 : 'KEY_0',
#        0 : 'KEY_PLAY',
#        0 : 'KEY_REWIND',
#        0 : 'KEY_FORWARD',
       67 : 'KEY_HELP',        # F1
#        0 : 'KEY_RECORD',
      127 : 'KEY_STOP',        # Pause
#        0 : 'KEY_RADIO',
      111 : 'KEY_UP',
      116 : 'KEY_DOWN',
      113 : 'KEY_LEFT',
      114 : 'KEY_RIGHT',
      104 : 'KEY_OK',          # NB Enter
#        0 : 'KEY_VOLUMEUP',
#        0 : 'KEY_VOLUMEDOWN',
      112 : 'KEY_CHANNELUP',   # pageup
      117 : 'KEY_CHANNELDOWN', # pagedown
#        0 : 'KEY_TEXT',
      106 : 'KEY_RED',         # NB DIV
       63 : 'KEY_GREEN',       # NB MUL
       82 : 'KEY_YELLOW',      # NB MINUS
       86 : 'KEY_BLUE',        # NB PLUS
#        0 : 'KEY_MENU',
#        0 : 'KEY_MENU_P',
#        0 : 'KEY_MENU_M',
#        0 : 'KEY_MENU_S',
       23 : 'KEY_TAB',
       37 : 'KEY_CTRL',
       64 : 'KEY_LEFTALT',
      108 : 'KEY_RIGHTALT',
       50 : 'KEY_LEFTSHIFT',
       22 : 'KEY_BACKSPACE',
       48 : 'KEY_APOSTROPHE',
       61 : 'KEY_SLASH',
       59 : 'KEY_COMMA',
       60 : 'KEY_DOT',
       21 : 'KEY_EQUAL',
       47 : 'KEY_SEMICOLON',
}

class X11Input(object):

    def __init__(self, xDisplay):
        """Create window, init OpenGL objects"""

        self.xDisplay = xDisplay

    def process_events (self):

        xlib_wrapper.XLockDisplay(self.xDisplay)

        res = None

        while xlib_wrapper.XPending ( self.xDisplay ):  
            xev = xlib_wrapper.XEvent()  
            xlib_wrapper.XNextEvent( self.xDisplay, ctypes.byref(xev) )  
            #print ""  
            #print "X EVENT " + repr(xev.type)
            #print ""  
            #if xev.type == xlib_wrapper.MotionNotify:  
                #print "moveto " + str(xev.xmotion.x) + "," + str(xev.xmotion.y)  
                #offset = (xev.xmotion.x, xev.xmotion.y)
                #window_y  =  (window_height - xev.xmotion.y) - window_height / 2.0;  
                #norm_y    =  window_y / (window_height / 2.0)  
                #window_x  =  xev.xmotion.x - window_width / 2.0  
                #norm_x    =  window_x / (window_width / 2.0)  
                #updatePos = True  

            if xev.type == xlib_wrapper.KeyPress:  
                print "keypress2 state=%s button=%s" % (repr(xev.xkey.state), repr(xev.xkey.keycode))  

                keycode = int(xev.xkey.keycode)
                if keycode in keymap:
                    res = keymap[keycode]

        xlib_wrapper.XUnlockDisplay(self.xDisplay)

        return res


