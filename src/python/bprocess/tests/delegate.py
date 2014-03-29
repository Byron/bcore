#-*-coding:utf-8-*-
"""
@package bcore.tests.processcontrol.delegate
@brief A delegate for testing process communication

@copyright 2013 Sebastian Thiel
"""
__all__ = []

import subprocess

from bcore.processcontrol import ProcessControllerDelegate
from butility import Path 

class TestCommunicatorDelegate(ProcessControllerDelegate):
    """Communicate with a process and see how that works"""
    __slots__ = ()
    
    def should_spawn_process(self):
        return True
    
    def process_filedescriptors(self):
        return (None, subprocess.PIPE, subprocess.PIPE)
    
    def communicate(self, process):
        # another test runs in here, but has no channel configured
        if process.stdout is None:
            return super(TestCommunicatorDelegate, self).communicate(process)
        # handle other test
        
        try:
            # output should be marker file
            lines = process.stdout.readlines()
            assert len(lines) == 1
            tmpfile = Path(lines[0].strip())
            tmpfile.remove()
        finally:
            res = super(TestCommunicatorDelegate, self).communicate(process) 
        return res

# end class TestCommunicator


class TestOverridesDelegate(TestCommunicatorDelegate):
    """Check for base class override handling"""
    __slots__ = ()
    
    def _assert_has_overridden_args(self, args, expected_result):
        """value is Boolean that should match the result"""
        result = False
        for arg in args:
            result |= arg.startswith('---')
        assert result == expected_result
            
    def prepare_environment(self, executable, env, args, cwd):
        """Custom args will remain here, but are interpreted"""
        self._assert_has_overridden_args(args, True)
        super(TestOverridesDelegate, self).prepare_environment(executable, env, args, cwd)
        self._assert_has_overridden_args(args, True)
        
        
    def pre_start(self, executable, env, args, cwd):
        """verify custom args don't remain"""
        self._assert_has_overridden_args(args, True)
        executable, env, args, cwd = super(TestOverridesDelegate, self).pre_start(executable, env, args, cwd)
        self._assert_has_overridden_args(args, False)
        return executable, env, args, cwd

    

# end class TestOverridesDelegate
