#-*-coding:utf-8-*-
"""
@package tx.core.component
@brief A framework to further modularize the code in the bcore framework.

@note when importing this module, we will put all exported items into the
buitin module to make it available everywhere without import. Its a vital
system, which should come at no extra effort.

@page components Component Framework

Notes
=====

* Singletons - via created instances that may derive from Singleton
* Instantiation - yes, but as separate method
* Service = instance providing some interface(s)
* natural inheritance - no special implements function required
* support for clonable types (by interface) - no, not interface instantiation contolled using interface description
* Multi-inheritance - yes, naturally
* referencing (strong, weak) and cleanup (deletion). See similar implementation in MRV event system - no, just 
  strong referencing, deletion when environment gets replaced, popped.
* services owned by environment, or by caller, depending on the way the service is retrieved.

@todo remove notes when implementation is done

@copyright 2012 Sebastian Thiel
"""

# make everything available from this level right away
from . import base

# make sure people can get the most fundamental implementation in this package
from .base import *
from .exceptions import *
from .properties import *

# also import the interfaces that are useful pipeline wide

def initialize():
    """Place all modules into the builtin module"""
    import __builtin__
    for name in  base.__for_builtin__:
        setattr(__builtin__, name, globals()[name])
    # end for each item to put into builtin
        
