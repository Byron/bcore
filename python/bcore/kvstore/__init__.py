#-*-coding:utf-8-*-
"""
@package bcore.core.kvstore
@brief A package with configuration access for reading and writing

@page kvstore KeyValue-Store Framework

@copyright 2012 Sebastian Thiel
"""
import sys
import os

# W0403 Allow relative import in this case, absolute imports don't work here
# pylint: disable-msg=W0403

def _init_yaml_persistence():
    """Assure the yaml module is setup so that it can handle ordered dicts when serializing data"""
    # for now we have a yaml dependency (json would be nicer as its supported out of the box
    # We try to use the system libraries, as those might have CYaml support. Otherwise we use
    # our own pure-python implementatino
    try:
        import yaml
    except ImportError:
        # use our version
        lib_path = os.path.join(os.path.dirname(__file__), 'lib')
        sys.path.append(lib_path)
        try:
            import yaml
        except ImportError:
            raise ImportError("Failed to import yaml, even using our own library at %s")
        #end handle yaml
    # end handle exception
    
    # set the module to be part of us
    sys.modules['yaml'] = yaml
    
    
    # Setup persistence
    import persistence
    persistence.initialize_yaml_overrides()
    

_init_yaml_persistence()


from .base import *
from .serialize import *
from .persistence import *
from .schema import *
from .diff import *
from .types import *


