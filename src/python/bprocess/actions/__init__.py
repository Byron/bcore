#-*-coding:utf-8-*-
"""
@package bprocess.actions
@brief Package containing the actions implementation, a generalized utility to so something when a program is started

Actions are the application of the command pattern to do anything.

@note standard actions will always be available and are loaded by default.

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from .base import *
from .copy import *
from .schema import *
