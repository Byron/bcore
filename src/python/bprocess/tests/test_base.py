#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_base
@brief tests for bprocess

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from future.builtins import object
__all__ = []

if __name__ == '__main__':
    print(sys.argv)

import sys
import os
import tempfile

import bapp

from butility.tests import TestCase
from bprocess import *
from bapp.tests import (preserve_application,
                        with_application)
from butility import Path

import subprocess


class TestCommand(object):
    """Create a marker file upon execution"""
    __slots__ = ()
    
    marker = Path(tempfile.mktemp())
    
    def execute(self):
        self.marker.touch()
        # Output for the delegate to receive
        print(self.marker)

# end class TestCommand


class ITestMarkerInterface(object):
    """Just a marker to find something in the registry"""
    __slots__ = ()

    

# end class CustomTestInterface


class TestPluginLoading(object):
    """Setup an application and try to use a very specific plugin"""
    __slots__ = ()

    def execute(self):
        assert len(sys.argv) == 2
        use_settings = sys.argv[1] == 'settings'
        app = ProcessAwareApplication.new(load_plugins_from_settings = use_settings,
                                          load_plugins_from_trees = not use_settings)
        # that would only work if the plugin was loaded
        app.new_instance(ITestMarkerInterface)

# end class TestPluginLoading


class TestProcessController(ProcessController):
    """A controller tuned not to 'break out' of the test-sandbox by traversing up the hierarchy.
    Doing it this way seems easier than creating a custom Application instance for each test-case, and passing
    it to the ProcessController instance"""
    __slots__ = ()

    traverse_process_path_hierachy = False
    traverse_additional_path_hierachies = False
    load_user_settings = False

    def _filter_application_directories(self, dirs):
        return Path(__file__).dirname() / 'etc'

# end class TestProcessController


def pseudo_executable(bin_name):
    """@return full path to pseudo_executable based on the given executable basename"""
    return Path(__file__).dirname() / bin_name


class TestProcessControl(TestCase):
    """Tests for the process control engine"""
    __slots__ = ()
    
    @preserve_application
    def test_base(self):
        """test fundamentals"""
        # Now we could nicely mock the environment - lets do this once we have a CWD environment
        # For now its not too easy though
        # failure as foo cannot be found
        self.failUnlessRaises(EnvironmentError, lambda: TestProcessController(pseudo_executable('foo'), ('hello', 'world')).application())

    @preserve_application
    def test_python_execution(self):
        """we should be able to execute any code directly using the delegate, without spawning"""
        pctrl = TestProcessController(pseudo_executable('py-program'), list())
        
        process = pctrl.execute()
        assert process.returncode == 0

        prefix, at_prefix = TestProcessController.wrapper_arg_prefix, TestProcessController.wrapper_context_prefix
        args = ('---packages.py-program.delegate=ProcessControllerDelegate ----escaped-arg %s%s %s %s'
                        % (at_prefix, at_prefix, at_prefix, prefix)).split()
        pctrl = TestProcessController(pseudo_executable('py-program'), args)
        pctrl.application()
        
    @preserve_application
    def test_wrapper_args(self):
        """verify we can handle custom arguments"""
        cmd_path = pseudo_executable('py-program-overrides')
        self.failUnlessRaises(DisplayHelpException, TestProcessController(cmd_path, '---foo=bar ---help'.split()).execute)
        
        self.failUnlessRaises(ValueError, TestProcessController(cmd_path, ['---foo']).execute)
        
        pctrl = TestProcessController(cmd_path, '---foo=bar ---hello.world=42'.split())
        assert pctrl.execute().returncode == 0

        # Override the python version, to something that doesn't exist
        version = '0.2.3'
        new_exec = '/absolute/path/exec'
        pctrl = TestProcessController(cmd_path, ('---packages.python.executable=%s' % new_exec).split())
        assert pctrl.executable() == new_exec, 'cmd line override should have worked'

        # we can't set the custom override to a directory that doesn't exist
        for context in ('foobar', '/path/to/foobar.ext'):
            self.failUnlessRaises(ValueError, TestProcessController(cmd_path, ['@%s' % context]).application)
        # end for each context to check

        # try list parsing
        TestProcessController(cmd_path, ("---foo=['some','list','items']").split()).executable()
        
        # this one should fail, invalid value
        self.failUnlessRaises(ValueError, TestProcessController(cmd_path, ("---foo=[bar]").split()).executable)
        
    @preserve_application
    def test_execute_in_context(self):
        process = TestProcessController(pseudo_executable('py-program'), ['--hello', 'world']).execute_in_current_context()
        assert process.returncode == 1, "should not have understood our arguments"
        
        # now with self-driven communication
        process = TestProcessController(pseudo_executable('py-program')).execute_in_current_context(stdout=subprocess.PIPE)
        assert process.returncode is None
        # delete the file it creates
        os.remove(process.stdout.readlines()[0].strip())
        process.communicate()
        assert process.returncode == 0

    @preserve_application
    def test_delegate_finder(self):
        from .delegate import TestCommunicatorDelegate
        pctrl = TestProcessController(pseudo_executable('py-program-no-delegate'))
        tcd_name = TestCommunicatorDelegate.__name__
        assert type(pctrl.delegate()).__name__ == tcd_name, "The delegate should be looked up from the alias"

        pctrl = TestProcessController(pseudo_executable('py-program-delegate-via-requires'))
        assert type(pctrl.delegate()).__name__ == tcd_name

        # This one really tests remote configuration
        pctrl = TestProcessController(pseudo_executable('py-program-delegate-via-requires-in-remote-config'), ('---trace', 
            '---foo=bar'))
        assert type(pctrl.delegate()).__name__ == 'TestOverridesDelegate'

    @with_application(from_file=__file__)
    def test_nosetest_delegate(self):
        """brief docs"""
        pctrl = TestProcessController(pseudo_executable('nosetests-delegate'), ['---dry-run'], application=bapp.main())
        assert pctrl.execute().returncode == 0

    @preserve_application
    def test_process_plugin_loading(self):
        """Assure plugins are loaded from trees and using the settings"""
        for program in ('load-from-settings', 'load-from-directories'):
            pctrl = TestProcessController(pseudo_executable(program))
            assert pctrl.execute_in_current_context().returncode == 0
        # end for each program to test

    @preserve_application
    def test_iteration(self):
        """verify simple package iteration works (for those who want it)"""
        count = 0
        program = 'py-program-overrides'
        executable = pseudo_executable(program)
        args = ('---trace',)
        for package in TestProcessController(executable, args).iter_packages(program):
            count += 1
            assert isinstance(package, ProcessControllerPackageSpecification)
        # end for each package
        assert count > 1
        
        self.failUnlessRaises(EnvironmentError, TestProcessController(executable, args).iter_packages('foobar').__next__)
        
    @preserve_application
    def test_post_launch_info(self):
        """Just some basic tests"""
        info = ControlledProcessInformation()
        if not info.has_data():
            assert info.data() is None and info.process_data() is None
        else:
            pinfo = info.process_data()
            assert pinfo.executable.isfile()
            assert pinfo.executable.dirname().isdir()
            assert pinfo.id
            app = ProcessAwareApplication.new()
            assert bapp.main().context().settings().value_by_schema(process_schema).executable == pinfo.executable
        # end handle data
        assert ProcessAwareApplication.process_information() is info, "process information should be a singleton"
        
# end class TestProcessControl
