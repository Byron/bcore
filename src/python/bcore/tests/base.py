#-*-coding:utf-8-*-
"""
@package bcore.tests.base
@brief most fundamental types

@copyright 2012 Sebastian Thiel
"""

import unittest
import gc
import sys
import shutil
import tempfile
import inspect

import bcore
from butility.tests import (TestCaseBase,
                            TestInterfaceBase)
from butility import (make_path,
                      Path)

from bkvstore import KeyValueStoreSchema
# TODO
# from bprocess import (ProcessControllerDelegate,
#                       IPostLaunchProcessInformation)
from bcore.log import module_logger
from butility import wraps

import nose

log = module_logger('bcore.tests')


# ==============================================================================
## @name Base Classes
# ------------------------------------------------------------------------------
# Classes to use for all test-cases
## @{

class EnvironmentAwareTestCaseBase(TestCaseBase):
    """TODO: review this one !! Should be in bregistry, or however it is called then
    @warning Be sure that types involved in pipeline components are created within the function that tests them.
    Otherwise those types will affect other tests.
    """
    __slots__ = (
                    '_previous_stack_len'  # Previous length of the stack encountered before we ran a test
                )
    
    # -------------------------
    ## @name Subclass Overrides
    # @{
    
    ## File that this type lifes in. Useful for out-of-tree subtypes
    fixture_root = make_path(__file__).dirname()
    
    ## -- End Subclass Overrides -- @}

    # -------------------------
    ## @name Setup and Teardown
    # Instance-methods are called before/after each individual test.
    #
    # Class-methods are called once before/after all tests run.
    #
    # Override them to setup sandboxes and to clean up afterwards
    # @{
    
    def setUp(self):
        """Runs before each individual test to set it up"""
        # be sure each test has his own environment to be independent of others
        self._previous_stack_len = len(bcore.environment)
        bcore.environment.push(str(self))
    
    def tearDown(self):
        """Runs after each test case to clean up afterwards"""
        assert isinstance(bcore.environment.pop(until_size = self._previous_stack_len), list)


    ## -- End Setup and Teardown -- @}

# end class EnvironmentAwareTestCaseBase


# TODO
# class NosetestDelegate(ProcessControllerDelegate):
#     """This delegate does nothing more but to parse nose-specific arguments in the PostLaunch data structure.
#     It also provides functionality to pick up the previously stored information and launch nose from it
#     @note this requires nose to be available in the python path, ideally the wrapper provides it as well"""
#     __slots__ = ()
    
#     schema = KeyValueStoreSchema('nosetests', { 'args' : list })
    
#     def set_context_override(self, schema, value, noseargs):
#         """Store noseargs in our value"""
#         value.args.extend(noseargs)

#     def pre_start(self, executable, env, args, cwd):
#         """Parse out all arguments until '--' and place them into extra process information.
#         @note will place a new environment to assure we get those arguments over into the launched application"""
#         try:
#             sep_index = args.index('--')
#             noseargs = args[:sep_index]
#             self.DelegateEnvironmentOverrideType('NosetestsOverride').setup(self, self.schema, noseargs)
#             args = args[sep_index+1:]
            
#             log.info("Starting nosetest with args: %s", ' '.join(noseargs))
#         except ValueError:
#             log.info('No nosetests arguments found - specify them using <nosetest flags> -- <hostapplication flags>')
#         # end handle no special nosetests args
        
#         return super(NosetestDelegate, self).pre_start(executable, env, args, cwd)
        
#     # -------------------------
#     ## @name Interface
#     # @{
    
#     @classmethod
#     def start_nose(cls):
#         """Start nose with the arguments previously specified on the commandline
#         @return true if all tests succeeded, false on failure"""
#         kvstore = new_service(IPostLaunchProcessInformation).as_kvstore()
#         value = kvstore.value(cls.schema.key(), cls.schema)
        
#         return nose.main(argv=['nosetests'] + value.args)
#     ## -- End Interface -- @}


# class NoseStartScriptDelegate(NosetestDelegate):
#     """Provides a path to the script that, if executed, starts up nose with the required arguments.
#     Its interface facilitates injecting the script into the arguments of the called process"""
#     __slots__ = ()
    
#     def entry_script_path(self):
#         """@return path to python script that can serve as entrypoint"""
#         return Path(__file__).dirname() / 'start-nose.py'
        
#     @bcore.abstractmethod
#     def modify_args(self, args, script_path):
#         """@return modified argument list containing entry_script_path() in a way that causes the hostapplication
#         to execute it
#         @param args program flags to modify
#         @param script_path path to the script that is to be injected so that the program will execute it
#         @note called from pre_start"""

#     def pre_start(self, executable, env, args, cwd):
#         executable, env, args, cwd = super(NoseStartScriptDelegate , self).pre_start(executable, env, args, cwd)
#         args = self.modify_args(args, self.entry_script_path())
#         assert isinstance(args, (list, tuple))
#         return (executable, env, args, cwd)

# # end class NoseStartScriptDelegate


# ## -- End Base Classes -- @}


