#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_base
@brief tests for bprocess

@copyright 2012 Sebastian Thiel
"""
__all__ = ['TestProcessController']

import sys
import os

import tempfile

import bcore
from bcore.tests import TestCaseBase
from bprocess import *

from butility import Path

import subprocess


class TestCommand(object):
    """Create a marker file upon execution"""
    __slots__ = ()
    
    marker = Path(tempfile.mktemp())
    
    def execute(self):
        self.marker.touch()
        # Output for the delegate to receive
        print self.marker

# end class TestCommand

class TestProcessController(ProcessController):
    """A utility to prevent it from executing
    @note this type needs to be here not to end up on the environment stack of all test cases"""
    __slots__ = ()

    dry_run = True
    
    _auto_register_class_ = False
    _auto_register_instance_ = False
    
# end class TestProcessController

def pseudo_executable(bin_name):
    """@return full path to pseudo_executable based on the given executable basename"""
    return Path(__file__).dirname() / bin_name


class TestProcessControl(TestCaseBase):
    """Tests for the process control engine"""
    __slots__ = ()
    
    def test_base(self):
        """test fundamentals"""
        # Now we could nicely mock the environment - lets do this once we have a CWD environment
        # For now its not too easy though
        # failure as foo cannot be found
        self.failUnlessRaises(EnvironmentError, TestProcessController().init, pseudo_executable('foo'), ('hello', 'world'))

    def test_forced_spawn(self):
        """Verify that we can easily enforce a process to be spawned, without overwriting any 'natural' configuration"""
        pctrl = new_service(ProcessController).init(pseudo_executable('rvio'), list())
        assert type(pctrl) is ProcessController and not pctrl.dry_run

        assert pctrl.set_should_spawn_process_override(True) is None
        assert pctrl.execute().returncode == 255
        
    def test_python_execution(self):
        """we should be able to execute any code directly using the delegate, without spawning"""
        pctrl = new_service(ProcessController).init(pseudo_executable('py-program'), list())
        
        process = pctrl.execute()
        assert process.returncode == 0
        
    def test_custom_args(self):
        """verify we can handle custom arguments"""
        cmd_path = pseudo_executable('py-program-overrides')
        assert new_service(ProcessController).init(cmd_path, '---foo=bar ---help'.split()).execute().returncode == 0
        
        pctrl = new_service(ProcessController)
        self.failUnlessRaises(AssertionError, pctrl.init, cmd_path, ['---foo'])
        
        pctrl = new_service(ProcessController).init(cmd_path, '---foo=bar ---hello.world=42'.split())
        assert pctrl.execute().returncode == 0
        
    def test_execute_in_context(self):
        process = ProcessController().init(pseudo_executable('py-program'), ['--hello', 'world']).execute_in_current_context()
        assert process.returncode == 1, "should not have understood our arguments"
        
        # now with self-driven communication
        process = ProcessController().init(pseudo_executable('py-program')).execute_in_current_context(stdout=subprocess.PIPE)
        assert process.returncode is None
        # delete the file it creates
        os.remove(process.stdout.readlines()[0].strip())
        process.communicate()
        assert process.returncode == 0
        
    def test_iteration(self):
        """verify simple package iteration works (for those who want it)"""
        count = 0
        for package in ProcessController().iter_packages('tractor-maya-batch'):
            count += 1
            assert isinstance(package, ProcessControllerPackageSpecification)
        # end for each package
        assert count > 1
        
        self.failUnlessRaises(EnvironmentError, ProcessController().iter_packages('foobar').next)
        
    def test_post_launch_info(self):
        """Just some basic tests"""
        info = new_service(bcore.IPostLaunchProcessInformation)
        if not info.has_data():
            assert info.data() is None and info.process_data() is None
        else:
            pinfo = info.process_data()
            assert pinfo.executable.isfile()
            assert pinfo.bootstrap_dir.isdir()
            assert pinfo.id
            assert bcore.app().context().context().value_by_schema(process_schema).executable == pinfo.executable
        # end handle data
        
        

# end class TestProcessControl
