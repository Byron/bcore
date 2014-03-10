#-*-coding:utf-8-*-
"""
@package bcore.db.shotgun.orm
@brief A pythonic type system for shotgun

@copyright 2013 Sebastian Thiel
"""
import sys

from .base import *

def _initialize():
    """Set application default encoding to unicode !
    Otherwise we can see errors when trying to decode shotgun text
    If this is a problem, we can also set it on per property basis
    """
    # see http://geekforbrains.com/post/setting-the-default-encoding-in-python
    # its needed !!
    reload(sys)
    sys.setdefaultencoding('utf-8')
    
_initialize()
    

