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
# Cairo + OpenGL ES based direct console graphics for RaspberryPi
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

class PiGraphics(object):

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

    def _create_window(self, depthbuffer):
        """Opens up the OpenGL library and prepares a window for display"""

        b = bcm.bcm_host_init()
        assert b==0
        self.display = openegl.eglGetDisplay(EGL_DEFAULT_DISPLAY)
        assert self.display
        r = openegl.eglInitialize(self.display,0,0)
        assert r
        if depthbuffer:
            attribute_list = eglints((EGL_RED_SIZE, 8,
                                      EGL_GREEN_SIZE, 8,
                                      EGL_BLUE_SIZE, 8,
                                      EGL_ALPHA_SIZE, 8,
                                      EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
                                      EGL_DEPTH_SIZE, 16,
                                      EGL_NONE) )
        else:
            attribute_list = eglints((EGL_RED_SIZE, 8,
                                      EGL_GREEN_SIZE, 8,
                                      EGL_BLUE_SIZE, 8,
                                      EGL_ALPHA_SIZE, 8,
                                      EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
                                      EGL_NONE) )
                                                                    
        numconfig = eglint()
        config = ctypes.c_void_p()
        r = openegl.eglChooseConfig(self.display,
                                     ctypes.byref(attribute_list),
                                     ctypes.byref(config), 1,
                                     ctypes.byref(numconfig));
        assert r
        r = openegl.eglBindAPI(EGL_OPENGL_ES_API)
        assert r
        if VERBOSE:
            print 'numconfig=',numconfig
        context_attribs = eglints( (EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE) )
        self.context = openegl.eglCreateContext(self.display, config,
                                        EGL_NO_CONTEXT,
                                        ctypes.byref(context_attribs))
        assert self.context != EGL_NO_CONTEXT
        width = eglint()
        height = eglint()
        s = bcm.graphics_get_display_size(0,ctypes.byref(width),ctypes.byref(height))
        self.width = width.value
        self.height = height.value
        assert s>=0
        dispman_display = bcm.vc_dispmanx_display_open(0)
        dispman_update = bcm.vc_dispmanx_update_start( 0 )
        dst_rect = eglints( (0,0,width.value,height.value) )
        src_rect = eglints( (0,0,width.value<<16, height.value<<16) )
        assert dispman_update
        assert dispman_display
        dispman_element = bcm.vc_dispmanx_element_add ( dispman_update, dispman_display,
                                  0, ctypes.byref(dst_rect), 0,
                                  ctypes.byref(src_rect),
                                  DISPMANX_PROTECTION_NONE,
                                  0 , 0, 0)
        bcm.vc_dispmanx_update_submit_sync( dispman_update )
        nativewindow = eglints((dispman_element,width,height));
        nw_p = ctypes.pointer(nativewindow)
        self.nw_p = nw_p
        self.surface = openegl.eglCreateWindowSurface( self.display, config, nw_p, 0)
        assert self.surface != EGL_NO_SURFACE
        r = openegl.eglMakeCurrent(self.display, self.surface, self.surface, self.context)
        assert r

    def __init__(self,depthbuffer=False):
        """Create window, init OpenGL objects"""

        global bcm, opengles, openegl

        bcm = ctypes.CDLL('libbcm_host.so')
        opengles = ctypes.CDLL('libGLESv2.so')
        openegl = ctypes.CDLL('libEGL.so')

        self._create_window(depthbuffer)

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

        # create texture
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
            print "PiGraphics.__init__() done."

    def get_cairo_ctx (self):
        return self.ctx

       
    def swap_buffers (self):
 
        opengles.glTexImage2D(GL_TEXTURE_2D, 0, GL_BGRA_EXT, self.texture_width, self.texture_height, 0, GL_BGRA_EXT, GL_UNSIGNED_BYTE, self.img)

        opengles.glClear(GL_COLOR_BUFFER_BIT)

        opengles.glUseProgram(self.program)

        opengles.glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.vertices)
        opengles.glEnableVertexAttribArray(0)
        opengles.glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        self.check()

        openegl.eglSwapBuffers(self.display, self.surface);
        self.check()      

#
# main
#

if __name__ == "__main__":

    # 
    # setup display
    #
    
    gfx = PiGraphics()
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
        time.sleep(1)


