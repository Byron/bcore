#-*-coding:utf-8-*-
"""
@package bkvstore
@brief A package with configuration access for reading and writing

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
# Allow better imports !
from __future__ import absolute_import

from butility import (Version,
                      Path,
                      load_package)
__version__ = Version("0.1.0")

import sys
import os

def _init_yaml_persistence():
    """Assure the yaml module is setup so that it can handle ordered dicts when serializing data"""
    # for now we have a yaml dependency (json would be nicer as its supported out of the box
    # We try to use the system libraries, as those might have CYaml support. Otherwise we use
    # our own pure-python implementation
    try:
        import yaml
    except ImportError:
        # use our version
        try:
            yaml_package_dir = Path(__file__).dirname() / 'yaml-builtin' / ('py%i' % sys.version_info.major)
            yaml = load_package(yaml_package_dir, 'yaml')
        except ImportError:
            raise ImportError("Failed to import yaml, even using our own library at bkvstore.yaml")
        #end handle yaml
    # end handle exception
    
    # set the module to be part of us
    sys.modules['yaml'] = yaml
    
    # Setup persistence
    from . import persistence
    persistence.initialize_yaml_overrides()

# end  initializer

_init_yaml_persistence()


from .base import *
from .serialize import *
from .persistence import *
from .schema import *
from .diff import *
from .types import *
from .utility import *
