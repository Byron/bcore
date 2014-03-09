#-*-coding:utf-8-*-
"""
@package tx.tests.base
@brief most fundamental types

@copyright 2012 Sebastian Thiel
"""
__all__ = ['unittest', 'make_path', 'with_rw_directory', 'TestCaseBase', 'TestInterfaceBase', 'swap_globals',
            'TempRWDirProvider', 'NosetestDelegate', 'skip_not_implemented']

import unittest
import gc
import sys
import shutil
import tempfile
import inspect

import bcore
from bcore.path import (
                        make_path,
                        Path
                    )

from bcore.core.kvstore import (
                                KeyValueStoreSchema,
                                KeyValueStoreProvider
                            )
from bcore.processcontrol import (
                                        ProcessControllerDelegate,
                                        IPostLaunchProcessInformation
                                    )
from bcore.core.logging import module_logger
from bcore.utility import wraps

import nose

log = module_logger('tx.tests')

# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

def swap_globals(new_stack):
    """switches the environment stack to a new stack"""
    old_stack = tx.environment
    tx.environment = new_stack
    return old_stack

## -- End Utilities -- @}



# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
# Decorators to use with methods in test-cases
## @{

def _maketemp(*args, **kwargs):
    """Wrapper around default tempfile.mktemp to fix an osx issue"""
    tdir = tempfile.mktemp(*args, **kwargs)
    if sys.platform == 'darwin':
        tdir = '/private' + tdir
    return make_path(tdir)


class TempRWDirProvider(object):
    """Simple type which provides a temporary directory during its lifetime, deleting it when it is deleted"""
    __slots__ = ('_dir')

    def __init__(self):
        self._dir = _maketemp()
        self._dir.mkdir()
        
    def __del__(self):
        shutil.rmtree(self._dir)
        
    def dir(self):
        return self._dir
    

# end class TempRWDirProvider

def with_rw_directory(func):
    """Create a temporary directory which can be written to, pass it as first
    argument to decorated method.

    Additionally, remove the directory if the test succeeds, but leave it
    otherwise to aid additional debugging.

    The temporary directory will be named like the name of the wrapped function,
    suffixed with alphanumeric characters to make it unique.

    Example:
    @snippet bcore/tests/doc/test_examples.py with_rw_directory
    """
    @wraps(func)
    def wrapper(self):
        path = make_path(_maketemp(prefix=func.__name__))
        path.mkdir()
        keep = False
        try:
            try:
                return func(self, path)
            except Exception, err:
                print >> sys.stderr, ("Test %s.%s failed with error %s: '%s', output is at %r"
                            % (type(self).__name__, type(err), str(err), func.__name__, path))
                keep = True
                raise
            #end be informed about failure
        finally:
            # Need to collect here to be sure all handles have been closed. It appears
            # a windows-only issue. In fact things should be deleted, as well as
            # memory maps closed, once objects go out of scope. For some reason
            # though this is not the case here unless we collect explicitly.
            if not keep:
                gc.collect()
                shutil.rmtree(path)
            #end if not keep
        #end handle exception
    #end wrapper
    return wrapper
    
def skip_not_implemented(func):
    """Convert NotImplementedError exceptions into SkipTest"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except NotImplementedError:
            raise nose.SkipTest
        # end convert exception
    # end wrapper
    return wrapper
    

## -- End Decorators -- @}


# ==============================================================================
## @name MetaClasses
# ------------------------------------------------------------------------------
## @{

class GlobalsItemDeletorMetaCls(tx.MetaBase):
    """Utiltiy to prevent base implementations of tests to be picked up by nose as the metacls
    will delete the given name from the globals.
    
    Types using this metaclass may set the _remove_from_globals classmethod accordingly which 
    iterable of strings to remove from the globals the type was created in .
    """
    
    _remove_from_globals_fun_name = '_remove_from_globals'
    
    def __new__(metacls, name, bases, clsdict):
        new_type = super(GlobalsItemDeletorMetaCls, metacls).__new__(metacls, name, bases, clsdict)
        
        remove_those = list()
        for typ in new_type.mro():
            remove_those += list(getattr(typ, metacls._remove_from_globals_fun_name, lambda: list())())
        # accumulate names to remove
        
        if remove_those and name not in remove_those:
            mod = __import__(new_type.__module__, globals(), locals(), new_type.__module__)
            for name_string in remove_those:
                try:
                    delattr(mod, name_string)
                except AttributeError:
                    pass
                # end remove item if possible
            # end for each name_string
        # end  handle deletion
        return new_type
        
        
class TestInterfaceMetaCls(GlobalsItemDeletorMetaCls):
    """Adds decorators to test-cases
    
    - Convert NotImplementedError exceptions to SkiptTest. 
      + Skipping tests should be something we see, usually everything should be implemented.
        If that is not possible, the interface is too specific
    """
    def __new__(metacls, name, bases, clsdict):
        for key, value in clsdict.iteritems():
            if inspect.isroutine(value) and key.startswith('test_'):
                clsdict[key] = skip_not_implemented(value)
            # end if we have a test
        # end for each item
        return super(TestInterfaceMetaCls, metacls).__new__(metacls, name, bases, clsdict)
        
    
## -- End MetaClasses -- @}



# ==============================================================================
## @name Base Classes
# ------------------------------------------------------------------------------
# Classes to use for all test-cases
## @{

class TestCaseBase(unittest.TestCase):
    """A base type for all test cases, providing additional utilities
    for every-day testing

    See the utility functions for more information
    @warning Be sure that types involved in pipeline components are created within the function that tests them.
    Otherwise those types will affect other tests.
    """
    __slots__ = (
                    '_previous_stack_len'  # Previous length of the stack encountered before we ran a test
                )
    
    # -------------------------
    ## @name Subclass Overrides
    # Subclasses may configure this base by setting those variables
    # @{
    
    ## Subdirectory to the ./fixtures root
    fixture_subdir = ''
    
    ## File that this type lifes in. Useful for out-of-tree subtypes
    fixture_root = make_path(__file__).dirname()
    
    ## -- End Subclass Overrides -- @}

    # -------------------------
    ## @name Utilities
    # Utilities to obtain input files for test cases
    # @{

    @classmethod
    def fixture_path(cls, filename):
        """Provide a path into the fixture directory
        @param cls
        @param filename relative path to or plain filename describing the file you
        would like to get an absolute path for, i.e. 'myfile.ext', 'directory/myfile.ext'e
        @return absolute tx.path into the fixture repository
        """
        return make_path(cls.fixture_root / 'fixtures' / cls.fixture_subdir / filename)
    ## -- End Utilities -- @}

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
        self._previous_stack_len = len(tx.environment)
        tx.environment.push(str(self))
    
    def tearDown(self):
        """Runs after each test case to clean up afterwards"""
        assert isinstance(tx.environment.pop(until_size = self._previous_stack_len), list)

    @classmethod
    def setUpClass(cls):
        """Runs one before all test cases run."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Runs once after all test cases were run"""
        pass

    ## -- End Setup and Teardown -- @}

# end class TestCaseBase


class TestInterfaceBase(TestCaseBase):
    """A base implementation for generic interface tests
    
    Subtypes are tests cases for specific interface, which in turn are derived from by test cases who which
    to test an actual interface implementation.
    
    Interface test cases may access a fresh instance of their interface in each test.
    """
    __slots__ = ('_instance')
    __metaclass__ = TestInterfaceMetaCls
    
    @classmethod
    def _remove_from_globals(cls):
        """@return always our typename if it is a direct decendent of this type"""
        name = 'TestInterfaceBase'
        if name in (base.__name__ for base in cls.__bases__) and name != cls.__name__:
            return [cls.__name__]
        return list()
    
    ## Contains the previous tx.environment stack for the duration of a test
    _prev_stack = None
    ## previous size of the stack before running the test
    _prev_size = None
    
    # -------------------------
    ## @name Subclass Configuration
    # @{
    
    ## the type implementing the IHostApplication interface
    ## Must be set by derived class
    subclass_type = None
    
    ## If True, we will not swap in an empty stack, but reuse the current one. Additonal Environments will be 
    ## removed when the tests ran.
    ## If False, the whole stack will be swapped with a new, fresh one
    keep_environment_stack = False
    
    
    ## -- End Subclass Configuration -- @}
    
    def setUp(self):
        """Assure subclasses can access a fres instance. Will skip subclasses that didn't setup their type.
        Also, make sure that registration of newly created types doesn't affect the global environment stack"""
        if self.subclass_type is None:
            raise nose.SkipTest
        
        if self.keep_environment_stack:
            super(TestInterfaceBase, self).setUp()
        else:
            self._prev_stack = swap_globals(type(tx.environment)())
        # end handle stack
        
        self._instance = self.subclass_type()
        
    def tearDown(self):
        del(self._instance)
        if self.keep_environment_stack:
            super(TestInterfaceBase, self).tearDown()
        else:
            swap_globals(self._prev_stack)
        # end handle keep stack

# end class TestInterfaceBase


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
            self.DelegateEnvironmentOverrideType('NosetestsOverride').setup(self, self.schema, noseargs)
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
        kvstore = new_service(IPostLaunchProcessInformation).as_kvstore()
        value = kvstore.value(cls.schema.key(), cls.schema)
        
        return nose.main(argv=['nosetests'] + value.args)
    ## -- End Interface -- @}


class NoseStartScriptDelegate(NosetestDelegate):
    """Provides a path to the script that, if executed, starts up nose with the required arguments.
    Its interface facilitates injecting the script into the arguments of the called process"""
    __slots__ = ()
    
    def entry_script_path(self):
        """@return path to python script that can serve as entrypoint"""
        return Path(__file__).dirname() / 'start-nose.py'
        
    @tx.abstractmethod
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


