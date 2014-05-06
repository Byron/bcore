#-*-coding:utf-8-*-
"""
@package be.tests.be_subcmd
@brief a subcommand for be, for testing only

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['BeSubCommand']


import bapp
from be import BeSubCommand


class TestCommand(BeSubCommand, bapp.plugin_type()):
    """@todo documentation"""
    __slots__ = ()

    name = "hello"
    version = '0.0.0'
    description = "prints hello world"

    def execute(self, args, remaining_args):
        print "hello world"
        return self.SUCCESS

# end class TestCommand
