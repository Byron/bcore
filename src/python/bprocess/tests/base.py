#-*-coding:utf-8-*-
"""
@package bprocess.tests.base
@brief Utilities for all kinds of testing tasks

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['NosetestDelegate', 'with_application']


import logging

import bapp
from bkvstore import KeyValueStoreSchema
from bprocess import (ProcessControllerDelegate,
                      ControlledProcessInformation)
from butility import ( abstractmethod,
                       wraps,
                       Path )
from bapp.tests import preserve_application


logging.getLogger('bprocess.tests.base')


# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

def with_application(fun):
    """A decorator which assures that our particular test configuration is loaded specifically, without
    traversing the hiararchy in order to not be dependent on whatever assembly we are in"""
    @wraps(fun)
    def wrapper(*args, **kwargs):
        print Path(__file__).dirname() / 'etc'
        app = bapp.Application.new(settings_trees=Path(__file__).dirname() / 'etc', 
                                   settings_hierarchy=False,
                                   user_settings=False)
        return fun(*args, **kwargs)
    # end wrapper

    return wrapper

## -- End Decorators -- @}


# ==============================================================================
# @name Base Classes
# ------------------------------------------------------------------------------
# Classes to use for all test-cases
# # @{

class NosetestDelegate(ProcessControllerDelegate):
    """This delegate does nothing more but to parse nose-specific arguments in the PostLaunch data structure.
    It also provides functionality to pick up the previously stored information and launch nose from it
    @note this requires nose to be available in the python path, ideally the wrapper provides it as well"""
    __slots__ = ()
    
    schema = KeyValueStoreSchema('nosetests', { 'args' : list })
    
    def set_context_override(self, schema, value, noseargs):
        """Store noseargs in our value"""
        value.args.extend(noseargs)

    def pre_start(self, executable, env, args, cwd):
        """Parse out all arguments until '--' and place them into extra process information.
        @note will place a new environment to assure we get those arguments over into the launched application"""
        try:
            sep_index = args.index('--')
            noseargs = args[:sep_index]
            self.DelegateContextOverrideType('NosetestsOverride').setup(self, self.schema, noseargs)
            args = args[sep_index+1:]
            
            log.info("Starting nosetest with args: %s", ' '.join(noseargs))
        except ValueError:
            log.info('No nosetests arguments found - specify them using <nosetest flags> -- <hostapplication flags>')
        # end handle no special nosetests args
        
        return super(NosetestDelegate, self).pre_start(executable, env, args, cwd)
        
    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def start_nose(cls):
        """Start nose with the arguments previously specified on the commandline
        @return true if all tests succeeded, false on failure"""
        kvstore = ControlledProcessInformation().as_kvstore()
        value = kvstore.value(cls.schema.key(), cls.schema)

        import nose        
        return nose.main(argv=['nosetests'] + value.args)
    ## -- End Interface -- @}


class NoseStartScriptDelegate(NosetestDelegate):
    """Provides a path to the script that, if executed, starts up nose with the required arguments.
    Its interface facilitates injecting the script into the arguments of the called process"""
    __slots__ = ()
    
    def entry_script_path(self):
        """@return path to python script that can serve as entrypoint"""
        return Path(__file__).dirname() / 'start-nose.py'
        
    @abstractmethod
    def modify_args(self, args, script_path):
        """@return modified argument list containing entry_script_path() in a way that causes the hostapplication
        to execute it
        @param args program flags to modify
        @param script_path path to the script that is to be injected so that the program will execute it
        @note called from pre_start"""

    def pre_start(self, executable, env, args, cwd):
        executable, env, args, cwd = super(NoseStartScriptDelegate , self).pre_start(executable, env, args, cwd)
        args = self.modify_args(args, self.entry_script_path())
        assert isinstance(args, (list, tuple))
        return (executable, env, args, cwd)

# end class NoseStartScriptDelegate

## -- End Base Classes -- @}

