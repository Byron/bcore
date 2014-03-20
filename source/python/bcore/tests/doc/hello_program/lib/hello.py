
import sys
import bcore.cmd

class HelloWorldCommand(bcore.cmd.CommandBase):
    __slots__ = ()
    
    name = 'hello'
    version = '1.0.0'
    description = 'just an example'
    
    def execute(self, args, remaining_argrs):
        print 'hello world'
        return 0

# end class HelloWorldCommand
