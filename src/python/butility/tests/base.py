#-*-coding:utf-8-*-
"""
@package butility.tests.base
@brief Contains utilities for use during testing

"""
from __future__ import division
from __future__ import print_function
from future.builtins import str
from future.builtins import object
from future.utils import with_metaclass
__all__ = ['unittest', 'with_rw_directory', 'TestCase', 'TestInterface',
            'TempRWDirProvider', 'skip_not_implemented', 'skip_on_travis_ci']

import unittest
import os
import gc
import sys
import shutil
import tempfile
import inspect

from butility import (Path,
                      Meta,
                      wraps)



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
    return Path(tdir)


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

    It will be provided as last argument of the wrapped function, and put into the os.environ at 'RW_DIR'

    Example:
    @snippet bapp/tests/doc/test_examples.py with_rw_directory
    """
    @wraps(func)
    def wrapper(self):
        path = Path(_maketemp(prefix=func.__name__))
        path.mkdir()
        keep = False
        prev_val = os.environ.get('RW_DIR')
        os.environ['RW_DIR'] = str(path)
        try:
            try:
                return func(self, path)
            except Exception as err:
                print(("Test %s.%s failed with error %s: '%s', output is at %r"
                            % (type(self).__name__, type(err), str(err), func.__name__, path)), file=sys.stderr)
                keep = True
                raise
            #end be informed about failure
        finally:
            if prev_val is not None:
                os.environ['RW_DIR'] = prev_val
            # end restore state
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
            import nose
            raise nose.SkipTest("NotImplemented")
        # end convert exception
    # end wrapper
    return wrapper

def skip_on_travis_ci(func):
    """All tests decorated with this one will raise SkipTest when run on travis ci.
    Use it to workaround difficult to solve issues"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if 'TRAVIS' in os.environ:
            import nose
            raise nose.SkipTest("Cannot run on travis-ci")
        # end check for travis ci
        return func(self, *args, **kwargs)
    # end wrapper
    return wrapper

## -- End Decorators -- @}


# ==============================================================================
## @name MetaClasses
# ------------------------------------------------------------------------------
## @{

class GlobalsItemDeletorMetaCls(Meta):
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
        for key, value in clsdict.items():
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

class TestCase(unittest.TestCase):
    """A base type for all test cases, providing additional utilities
    for every-day testing

    See the utility functions for more information
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Subclass Overrides
    # Subclasses may configure this base by setting those variables
    # @{
    
    ## Subdirectory to the ./fixtures root
    fixture_subdir = ''
    
    ## File that this type lifes in. Useful for out-of-tree subtypes
    fixture_root = Path(__file__).dirname()
    
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
        @return absolute butility.path into the fixture repository
        """
        return Path(cls.fixture_root / 'fixtures' / cls.fixture_subdir / filename)
    ## -- End Utilities -- @}

# end class TestCase


class TestInterface(with_metaclass(TestInterfaceMetaCls, TestCase)):
    """A base implementation for generic interface tests
    
    Subtypes are tests cases for specific interface, which in turn are derived from by test cases who which
    to test an actual interface implementation.
    
    Interface test cases may access a fresh instance of their interface in each test.
    """
    __slots__ = ('_instance')
    
    @classmethod
    def _remove_from_globals(cls):
        """@return always our typename if it is a direct decendent of this type"""
        name = 'TestInterface'
        if name in (base.__name__ for base in cls.__bases__) and name != cls.__name__:
            return [cls.__name__]
        return list()
    
    # -------------------------
    ## @name Subclass Configuration
    # @{
    
    ## the type implementing the IHostApplication interface
    ## Must be set by derived class
    subclass_type = None
    
    ## -- End Subclass Configuration -- @}
    
    def setUp(self):
        """Assure subclasses can access a fres instance. Will skip subclasses that didn't setup their type.
        Also, make sure that registration of newly created types doesn't affect the global environment stack"""
        if self.subclass_type is None:
            import nose
            raise nose.SkipTest
        
        self._instance = self.subclass_type()
        
    def tearDown(self):
        del(self._instance)
        super(TestInterface, self).tearDown()

# end class TestInterface


