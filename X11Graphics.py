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
# OpenGL ES based X11 windowed graphics output
#

VERBOSE = True

import ctypes
import time
import math
import os
import platform
import datetime
from base64 import b64decode

from egl.pyopengles import eglfloats, eglfloat, eglint, eglints, eglfloats, check
from egl.egl import *
from egl.gl2 import *
from egl.gl2ext import *

import cairo

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

class X11Graphics(object):

    def showlog(self,shader):
        """Prints the compile log for a shader"""
        N=1024
        log=(ctypes.c_char*N)()
        loglen=ctypes.c_int()
        opengles.glGetShaderInfoLog(shader,N,ctypes.byref(loglen),ctypes.byref(log))
        print log.value

    def showprogramlog(self,shader):
        """Prints the compile log for a program"""
        N=1024
        log=(ctypes.c_char*N)()
        loglen=ctypes.c_int()
        opengles.glGetProgramInfoLog(shader,N,ctypes.byref(loglen),ctypes.byref(log))
        print log.value

    def check(self):
        e=opengles.glGetError()
        if e:
            print hex(e)
            raise ValueError

    def _create_window(self, depthbuffer, name):
        """Opens up the OpenGL library and prepares a window for display"""

        xlib_wrapper.XInitThreads()

        #needs error checking  
        display = xlib_wrapper.XOpenDisplay (os.getenv ( "DISPLAY"))  
        self.xDisplay = display

        xlib_wrapper.XLockDisplay(self.xDisplay)

        screen = xlib_wrapper.XDefaultScreen (display)  
        root = xlib_wrapper.XDefaultRootWindow (display, screen)  
        windowAttributes=xlib_wrapper.XSetWindowAttributes()  
        windowAttributes.event_mask = (  
                     xlib_wrapper.PointerMotionMask  
                    | xlib_wrapper.KeyPressMask  
                    | xlib_wrapper.KeyReleaseMask  
                    | xlib_wrapper.ExposureMask  
                    | xlib_wrapper.ButtonPressMask  
                    | xlib_wrapper.ButtonReleaseMask  
                    )  

        # rpi PAL resolution
        self.width = 720
        self.height = 576

        window = xlib_wrapper.XCreateSimpleWindow (display, root, 10, 10, self.width, self.height, 1, 
                                                   xlib_wrapper.XBlackPixel (display, screen),
                                                   xlib_wrapper.XWhitePixel (display, screen))
        xlib_wrapper.XSelectInput (display, window, xlib_wrapper.PointerMotionMask  
                    | xlib_wrapper.KeyPressMask  
                    | xlib_wrapper.KeyReleaseMask  
                    | xlib_wrapper.ExposureMask  
                    | xlib_wrapper.ButtonPressMask  
                    | xlib_wrapper.ButtonReleaseMask)

        xattr=xlib_wrapper.XSetWindowAttributes()  
        xattr.override_redirect=False  
        xlib_wrapper.XChangeWindowAttributes(display,window,xlib_wrapper.CWOverrideRedirect,ctypes.byref(xattr))  

        xlib_wrapper.XMapWindow(display, window)  
        xlib_wrapper.XStoreName(display,window,name)  

        #now for the egl part  
        self.display= openegl.eglGetDisplay(display)  
        openegl.eglInitialize(self.display,None,None)  

        attribute_list = eglints((EGL_RED_SIZE, 8,
                                  EGL_GREEN_SIZE, 8,
                                  EGL_BLUE_SIZE, 8,
                                  EGL_ALPHA_SIZE, 8,
                                  EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
                                  EGL_DEPTH_SIZE, 16,
                                  EGL_NONE) )

        numconfig = eglint()

        print "numconfig: ", numconfig, self.display

        config = ctypes.c_void_p()
        r = openegl.eglChooseConfig(self.display,
                                     ctypes.byref(attribute_list),
                                     ctypes.byref(config), 1,
                                     ctypes.byref(numconfig));
        assert r
        r = openegl.eglBindAPI(EGL_OPENGL_ES_API)
        assert r

        self.surface = openegl.eglCreateWindowSurface(self.display, config, window, None,)  

        context_attribs = eglints( (EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE) )
        self.context = openegl.eglCreateContext(self.display, config,
                                        EGL_NO_CONTEXT,
                                        ctypes.byref(context_attribs))
        assert self.context != EGL_NO_CONTEXT

        openegl.eglMakeCurrent( self.display, self.surface, self.surface, self.context );  
        #xlib_wrapper.XSetInputFocus(display,root,xlib_wrapper.RevertToParent,xlib_wrapper.CurrentTime)  
        #xlib_wrapper.XSetInputFocus(display,window,xlib_wrapper.RevertToParent,xlib_wrapper.CurrentTime)  

        #gwa =  xlib_wrapper.XWindowAttributes()  
        #xlib_wrapper.XGetWindowAttributes ( self.xDisplay , window, ctypes.byref(gwa) )  
        #opengles.glViewport ( 0 , 0 , gwa.width , gwa.height )  
        #opengles.glClearColor ( ctypes.c_float(0.08) , ctypes.c_float(0.46) , ctypes.c_float(0.07) , ctypes.c_float(1.))   

        xlib_wrapper.XUnlockDisplay(self.xDisplay)

    def __init__(self, depthbuffer=False, name="X11Graphics"):
        """Create window, init OpenGL objects"""

        global opengles, openegl
    
        opengles = ctypes.CDLL('libGLESv2.so')
        openegl = ctypes.CDLL('libEGL.so')

        self._create_window(depthbuffer, name)

        xlib_wrapper.XLockDisplay(self.xDisplay)

        # Position attributes are in [-1, 1] x [-1, 1]. We can turn these into
        # texture coordinates ourselves, so we only take in one vertex attribute.
        self.vshader_source = ctypes.c_char_p(
        """
          attribute vec2 position;

          varying vec2 texcoord;

          void main() {
            gl_Position = vec4(position, 0.0, 1.0);
            // 720.0 / 1024.0 / 2.0 = 0.3515625
            // 576.0 / 1024.0 / 2.0 = 0.28125
            texcoord = vec2((position.x + 1.0) * 0.3515625, (1.0 - position.y) * 0.28125);
          }
        """)

        # Color is determined entirely by the texture.
        self.fshader_source = ctypes.c_char_p("""
          precision mediump float;
          uniform sampler2D frame;  

          varying vec2 texcoord; 

          void main() {
            gl_FragColor = texture2D(frame, texcoord);
          }
        """)

        vshader = opengles.glCreateShader(GL_VERTEX_SHADER);
        opengles.glShaderSource(vshader, 1, ctypes.byref(self.vshader_source), 0)
        opengles.glCompileShader(vshader);

        if VERBOSE:
            self.showlog(vshader)
            
        fshader = opengles.glCreateShader(GL_FRAGMENT_SHADER);
        opengles.glShaderSource(fshader, 1, ctypes.byref(self.fshader_source), 0);
        opengles.glCompileShader(fshader);

        if VERBOSE:
            self.showlog(fshader)

        self.program = opengles.glCreateProgram();
        opengles.glAttachShader(self.program, vshader);
        opengles.glAttachShader(self.program, fshader);
        opengles.glLinkProgram(self.program);

        # The position attribute is in slot 0.
        #self.binding = ((0, 'position'),)

        # Fill the viewport.
        self.vertices = eglfloats((-1.0, -1.0,
                                    1.0, -1.0,
                                   -1.0,  1.0,
                                    1.0,  1.0))

        # The will be uploaded to texture unit 0.
        opengles.glUseProgram(self.program)
        self.frameTextureUniformID = opengles.glGetUniformLocation(self.program, "frame")
        opengles.glUniform1i(self.frameTextureUniformID, 0)
        opengles.glUseProgram(0)

        # Let's make that texture!
        self.frameTextureID = eglint()
        opengles.glActiveTexture(GL_TEXTURE0) 
        opengles.glGenTextures(1, ctypes.byref(self.frameTextureID)) 
        opengles.glBindTexture(GL_TEXTURE_2D, ctypes.byref(self.frameTextureID)) 
        opengles.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        opengles.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        self.texture_width, self.texture_height = (1024, 1024)

        if VERBOSE:
            print "Cairo rendering..."

        surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, self.texture_width, self.texture_height)
        self.ctx = cairo.Context(surface)

        # take 16:9 aspect ration of our composite PAL display into account
        self.ctx.scale (0.75, 1.0)

        #
        # cairo -> open gl es texture
        #

        if VERBOSE:
            print "Cairo transfer..."

        data = surface.get_data()

        ImgArrayType = ctypes.c_ubyte * (self.texture_width*self.texture_height*3)
        self.img = ImgArrayType.from_buffer(data)

        if VERBOSE:
            print "display ready."

        opengles.glTexImage2D(GL_TEXTURE_2D, 0, GL_BGRA_EXT, self.texture_width, self.texture_height, 0, GL_BGRA_EXT, GL_UNSIGNED_BYTE, self.img)

        self.check()      

        opengles.glViewport(0, 0, self.width, self.height);
        opengles.glClearColor ( ctypes.c_float(0.08) , ctypes.c_float(0.46) , ctypes.c_float(0.07) , ctypes.c_float(1.))   

        self.scene     = []
        self.coffset   = 0

        if VERBOSE:
            print "X11Graphics.__init__() done."

        xlib_wrapper.XUnlockDisplay(self.xDisplay)
        
    def get_cairo_ctx (self):
        return self.ctx
       
    def swap_buffers (self):

        xlib_wrapper.XLockDisplay(self.xDisplay)

        opengles.glTexImage2D(GL_TEXTURE_2D, 0, GL_BGRA_EXT, self.texture_width, self.texture_height, 0, GL_BGRA_EXT, GL_UNSIGNED_BYTE, self.img)

        opengles.glClear(GL_COLOR_BUFFER_BIT)

        opengles.glUseProgram(self.program)

        opengles.glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.vertices)
        opengles.glEnableVertexAttribArray(0)
        opengles.glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        self.check()

        openegl.eglSwapBuffers(self.display, self.surface);
        self.check()     
 
        xlib_wrapper.XUnlockDisplay(self.xDisplay)



#
# main
#

if __name__ == "__main__":

    # 
    # setup display
    #
    
    gfx = X11Graphics()
    ctx = gfx.get_cairo_ctx()

    #
    # display demo gfx
    #

    ctx.set_source_rgb (0.1, 0.1, 1.0)
    ctx.paint()

    ctx.set_operator (cairo.OPERATOR_OVER)
    ctx.select_font_face ('Liberation Sans')
    ctx.set_font_size (72)

    ctx.set_source_rgb (1.0, 1.0, 1.0)

    ctx.move_to (100, 100)
    ctx.show_text ('Hello, World!')

    gfx.swap_buffers()

    while True:
        keysym = gfx.process_events()

        if keysym is not None:
            print "Keysym: %s" % keysym

        time.sleep(1)

