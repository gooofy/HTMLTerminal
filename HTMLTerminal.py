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
# OpenGL ES based HTML terminal for RaspberryPi
#

import ctypes
import time
import math
import os
import sys
import platform
import datetime
from base64 import b64decode
import traceback

import threading
import cairo

import zmq
import json

import ConfigParser
from os.path import expanduser

from Platform    import pi_version
from temperature import measure_temperatures
from logger      import ldebug, linfo, lerror, set_loglevel, LOG_DEBUG, LOG_INFO

import robinson

LED_UPDATE   =  50
TEMP_UPDATE  = 100

def hal_comm (socket, cmd, arg):

    reply = None

    try:

        rq = json.dumps ([cmd, arg])

        ldebug ("hal_comm: sending %s" % rq)
        socket.send (rq)

        #  Get the reply.
        message = socket.recv()

        reply = json.loads(message)
    except:
        traceback.print_exc()

    return reply


def _load_resource (resourcefn):
    global socket
    return b64decode(hal_comm (socket, 'LOAD_RESOURCE', resourcefn))


DRAW_SPEED = 32

SCMD_SET_SOURCE_RGBA    =  1
SCMD_PAINT              =  2
SCMD_SELECT_FONT_FACE   =  3
SCMD_SET_FONT_SIZE      =  4
SCMD_MOVE_TO            =  5
SCMD_SHOW_TEXT          =  6
SCMD_REL_LINE_TO        =  7
SCMD_CLOSE_PATH         =  8
SCMD_FILL               =  9
SCMD_SET_LINE_WIDTH     = 10
SCMD_SAVE               = 11
SCMD_RESTORE            = 12
SCMD_SET_SOURCE         = 13
SCMD_CLIP               = 14
SCMD_SET_SOURCE_SURFACE = 15

def text_extents(self, font_face, font_size, text):
    self.ctx.select_font_face (font_face)
    self.ctx.set_font_size (font_size)
    return self.ctx.text_extents (text)

def font_extents(self, font_face, font_size):
    self.ctx.select_font_face (font_face)
    self.ctx.set_font_size (font_size)
    return self.ctx.font_extents ()

class HAL(object):

    def __init__(self, gfx):

        self.gfx       = gfx
        self.ctx       = gfx.get_cairo_ctx()
        self.width     = gfx.width
        self.height    = gfx.height

        self.scene     = []
        self.coffset   = 0

        print "HAL.__init__() done."

    #
    # anim scene support stuff in a cairo context lookalike way
    #

    def scene_reset(self, counter):
        self.scene   = []
        self.coffset = counter

    def set_source_rgba (self, r, g, b, a):
        self.scene.append ( (SCMD_SET_SOURCE_RGBA, r, g, b, a) )

    def paint (self):
        self.scene.append ( (SCMD_PAINT, ) )

    def select_font_face (self, font_face):
        self.ctx.select_font_face (font_face)
        self.scene.append ( (SCMD_SELECT_FONT_FACE, font_face) )

    def set_font_size (self, font_size):
        self.ctx.set_font_size (font_size)
        self.scene.append ( (SCMD_SET_FONT_SIZE, font_size) )

    def set_line_width (self, w):
        self.scene.append ( (SCMD_SET_LINE_WIDTH, w) )

    def move_to (self, x, y):
        self.scene.append ( (SCMD_MOVE_TO, x, y) )

    def show_text (self, txt):
        self.scene.append ( (SCMD_SHOW_TEXT, txt) )

    def rel_line_to (self, x, y):
        self.scene.append ( (SCMD_REL_LINE_TO, x, y) )

    def close_path (self):
        self.scene.append ( (SCMD_CLOSE_PATH,) )

    def fill (self):
        self.scene.append ( (SCMD_FILL,) )

    def rectangle (self, x, y, w, h):
        self.move_to (x, y)
        self.rel_line_to (w, 0)
        self.rel_line_to (0, h)
        self.rel_line_to (-w, 0)
        self.close_path()

    def set_source (self, img):
        self.scene.append ( (SCMD_SET_SOURCE, img) )

    def set_source_surface (self, img, x, y):
        self.scene.append ( (SCMD_SET_SOURCE_SURFACE, img, x, y) )

    def clip (self):
        self.scene.append ( (SCMD_CLIP,) )

    def font_extents(self):
        return self.ctx.font_extents()

    def scene_html (self, html, css):
        html = robinson.html(html, css, self.width, _load_resource, text_extents, font_extents, self)
        html.render (self) 

    def scene_draw(self, counter):
      
        #
        # cairo
        #

        self.ctx.set_operator (cairo.OPERATOR_OVER)
        drawlimit = (counter - self.coffset) * DRAW_SPEED

        # render scene by executing commands

        for t in self.scene:

            drawlimit -= 1
            if drawlimit <= 0:
                break

            #print "SCMD: %s" % repr(t)

            scmd = t[0]
            if scmd == SCMD_SET_SOURCE_RGBA:
                self.ctx.set_source_rgba (t[1], t[2], t[3], t[4])
            elif scmd == SCMD_PAINT:
                self.ctx.paint()
            elif scmd == SCMD_SELECT_FONT_FACE:
                self.ctx.select_font_face (t[1])
            elif scmd == SCMD_SET_FONT_SIZE:
                self.ctx.set_font_size (t[1])
            elif scmd == SCMD_MOVE_TO:
                self.ctx.move_to (t[1], t[2])
            elif scmd == SCMD_SHOW_TEXT:
                self.ctx.show_text (t[1][:drawlimit])
                drawlimit -= len(t[1])
            elif scmd == SCMD_REL_LINE_TO:
                self.ctx.rel_line_to (t[1], t[2])
            elif scmd == SCMD_CLOSE_PATH:
                self.ctx.close_path()
            elif scmd == SCMD_FILL:
                self.ctx.fill()
            elif scmd == SCMD_SET_LINE_WIDTH:
                self.ctx.set_line_width (t[1])
            elif scmd == SCMD_SAVE:
                self.ctx.save()
            elif scmd == SCMD_RESTORE:
                self.ctx.restore()
            elif scmd == SCMD_SET_SOURCE:
                self.ctx.set_source(t[1])
            elif scmd == SCMD_CLIP:
                self.ctx.clip()
            elif scmd == SCMD_SET_SOURCE_SURFACE:
                self.ctx.set_source_surface(t[1], t[2], t[3])

        self.gfx.swap_buffers()        

def update_led():

    if USE_X11:
        return

    dt = datetime.datetime.now()
    led.led_write (dt.strftime("%H%M"))

class input_handler (object):

    def _process_events(self):

        try:
            key = self.inp.process_events()

            if key is not None:
                hal_comm (self.socket, 'KEYPRESS', key)
                return True
        except:
            traceback.print_exc()
            lerror("Input handler: EXCEPTION CAUGHT: %s" % traceback.format_exc())


        return False

    def _input_loop(self):

        while True:
            ldebug ("Input handler: _linput_loop iter")
            if not self._process_events():
                time.sleep(0.1)
            else:
                ldebug ("Input handler: INPUT EVENT HANDLED")
            


    def process_events(self):
        """public function to be called regularly, in effect on non-threaded X11 only"""

        global USE_X11

        if not USE_X11:
            return False   

        return self._process_events()
            
    def __init__(self, inp):

        global USE_X11

        self.inp = inp

        linfo("Input handler: connecting to server...")
        self.context = zmq.Context()
        self.socket  = self.context.socket(zmq.REQ)
        self.socket.connect ("tcp://%s:%s" % (host_getty, port_getty))

        if USE_X11:
            return
        
        # on rpi we handle input in separate thread for low latency

        linfo("Input handler: running on pi -> starting input thread")

        self.thread = threading.Thread (target=self._input_loop)
        self.thread.setDaemon(True)
        self.thread.start()


#
# main
#

USE_X11 = pi_version() == None
linfo ("Using X11: %s " % repr(USE_X11))

#
# load config, set up global variables
#

home_path = expanduser("~")

config = ConfigParser.RawConfigParser()
config.read("%s/%s" % (home_path, ".halrc"))

host_getty  = config.get("zmq", "host")
port_getty  = config.get("zmq", "port_getty")
port_gettyp = config.get("zmq", "port_gettyp")

sensor_inside  = config.get("term", "sensor_inside")
sensor_outside = config.get("term", "sensor_outside")
term_location  = config.get("term", "location")

# command line
if len(sys.argv) == 2 and sys.argv[1] == '-d':
    set_loglevel(LOG_DEBUG)
else:
    set_loglevel(LOG_INFO)
    

if not USE_X11:

    import led    
    from PiGraphics import PiGraphics
    from PiInput import PiInput

    gfx = PiGraphics ()
    inp = PiInput ()

else:

    from X11Graphics import X11Graphics
    from X11Input import X11Input

    gfx = X11Graphics (name = "HAL 9000")
    inp = X11Input (gfx.xDisplay)

#
# zmq connection to getty
#

context = zmq.Context()
socket  = context.socket(zmq.REQ)
socket.connect ("tcp://%s:%s" % (host_getty, port_getty))

# subscribe to broadcasts

socket_sub = context.socket(zmq.SUB)
socket_sub.connect ("tcp://%s:%s" % (host_getty, port_gettyp))

# messages we're interested in
socket_sub.setsockopt(zmq.SUBSCRIBE, 'DISPLAY_HTML')

# set up poller so we can do timeouts when waiting for messages
poller = zmq.Poller()
poller.register(socket_sub, zmq.POLLIN)

# 
# setup rendering engine + display
#

linfo("Setup rendering engine + display ...")
hal = HAL(gfx)
hal_comm (socket, 'TERM_BOOT', measure_temperatures(term_location, sensor_inside, sensor_outside))
update_led()

#
# input handler
#
linfo("Launching input handler...")
inp_handler = input_handler(inp)

#
# main loop
#

linfo("Starting main loop.")

quit = False
counter = 0
while not quit:

    if not inp_handler.process_events():

        # check for broadcast messages
        socks = poller.poll(10)

        if len(socks) > 0:
            for s,e in socks:
                cmd, data = s.recv().split(' ', 1)
                data = json.loads(data)
                ldebug("CMD is %s" % cmd)

                if cmd == 'DISPLAY_HTML':
                    ldebug("display html, counter=%d" % counter)
                    job_html, job_css, job_effect = data
                    try:
                        hal.scene_reset (0)
                        counter = 0 if job_effect == 1 else 32768
                        hal.scene_html (job_html, job_css)
                    except:
                        traceback.print_exc()
 
        hal.scene_draw (counter)
        counter += 1

        if counter % LED_UPDATE == 0:
            update_led()            
        if counter % TEMP_UPDATE == 0:
            hal_comm (socket, 'TEMPERATURE', measure_temperatures(term_location, sensor_inside, sensor_outside))

