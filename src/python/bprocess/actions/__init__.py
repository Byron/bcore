#-*-coding:utf-8-*-
"""
@package bcore.processcontrol.actions
@brief Package containing the actions implementation, a generalized utility to so something when a program is started

Actions are the application of the command pattern to do anything.

@note standard actions will always be available and are loaded by default.

@copyright 2013 Sebastian Thiel
"""
from .base import *
from .copy import *
from .schema import *
