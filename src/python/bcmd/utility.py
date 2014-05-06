#-*-coding:utf-8-*-
"""
@package bcmd.utility
@brief Some utilities for general command use

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['CommandArgumentParser', 'ArgparserHandledCall']

import sys
from .argparse import ArgumentParser


class ArgparserHandledCall(Exception):
    """An exception to indicate the arg parser handled the logic already.
    This usually happens if the commandline was called in help mode, or when showing the version"""
    __slots__ = 'message'
    def __init__(self, message):
        self.message = message
        

class CommandArgumentParser(ArgumentParser):
    """Our version of the argument parser which will not exit on error, but raise instead"""
    __slots__ = ()

    def exit(self, status=0, message=None):
        """Raise on error, instead of exiting
        @return status in case there is no message (i.e. the parser just wanted to exit)"""
        if status == 0:
            raise ArgparserHandledCall(message) 
            
        # reraise if possible
        exc_type, value, traceback = sys.exc_info()
        if value:
            raise
        else:
            assert message, "should have gotten an argparser message"
            raise Exception(message)
        # END options
    

# end class CommandArgumentParser

