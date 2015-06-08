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
# simple logging framework
#

import syslog
import datetime

LOG_DEBUG = 0
LOG_INFO  = 1
LOG_ERROR = 2

PROC_TITLE = 'hal_term'
LOG_LEVEL  = LOG_DEBUG
HAL_LOG_SYSLOG  = False

def set_loglevel (level):
    global LOG_LEVEL
    LOG_LEVEL = level

def log (level, msg):

    global LOG_LEVEL, HAL_LOG_SYSLOG

    if level < LOG_LEVEL:
        return

    if HAL_LOG_SYSLOG:
        syslog.syslog (msg)
    else:
        print "%s %s: %s" % (datetime.datetime.now().strftime ("%b %d %H:%M:%S"), PROC_TITLE, msg)

def ldebug (msg):
    log (LOG_DEBUG, msg)

def linfo (msg):
    log (LOG_INFO, msg)

def lerror (msg):
    log (LOG_ERROR, msg)

