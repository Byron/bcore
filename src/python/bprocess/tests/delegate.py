#-*-coding:utf-8-*-
"""
@package bprocess.tests.delegate
@brief A delegate for testing process communication

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = []

import subprocess

from bprocess import (ProcessControllerDelegate,
                      ProcessController,
                      process_schema)
from butility import Path 


class TestCommunicatorDelegate(ProcessControllerDelegate):
    """Communicate with a process and see how that works"""
    __slots__ = ()
    
    def launch_mode(self):
        return self.LAUNCH_MODE_CHILD
    
    def process_filedescriptors(self):
        return (None, subprocess.PIPE, subprocess.PIPE)
    
    def communicate(self, process):
        # another test runs in here, but has no channel configured
        if process.stdout is None:
            return super(TestCommunicatorDelegate, self).communicate(process)
        # handle other test
        
        try:
            # output should be marker file
            err_lines = process.stderr.readlines()
            assert not err_lines
            lines = process.stdout.readlines()
            assert len(lines) == 1
            tmpfile = Path(lines[0].strip())
            tmpfile.remove()
        finally:
            res = super(TestCommunicatorDelegate, self).communicate(process) 
        assert res.returncode == 0, "There should have been no error"
        return res

# end class TestCommunicator

class TestOverridesDelegate(TestCommunicatorDelegate):
    """Check for base class override handling"""
    __slots__ = ()
    
    def _assert_has_overridden_args(self, args, expected_result):
        """value is Boolean that should match the result"""
        prefix = ProcessController.wrapper_arg_prefix
        raw_args = self._app.context().settings().value_by_schema(process_schema).raw_arguments
        has_bootstrapper_arg = any(arg for arg in raw_args if arg.startswith(prefix))
        assert not any(arg for arg in args if arg.startswith(prefix))
        assert has_bootstrapper_arg == expected_result
            
    def prepare_context(self, executable, env, args, cwd):
        """Custom args will remain here, but are interpreted"""
        self._assert_has_overridden_args(args, True)
        super(TestOverridesDelegate, self).prepare_context(executable, env, args, cwd)
        self._assert_has_overridden_args(args, True)
        
        
    def pre_start(self, executable, env, args, cwd, resolve):
        """verify custom args don't remain"""
        self._assert_has_overridden_args(args, True)
        executable, env, args, cwd = super(TestOverridesDelegate, self).pre_start(executable, env, args, cwd, resolve)
        return executable, env, args, cwd

    

# end class TestOverridesDelegate
