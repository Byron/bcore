#-*-coding:utf-8-*-
"""
@package be.tests.test_cmd

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

from . import BeTestCase

import bapp
from bapp.tests import with_application
from bcmd import SubCommandBase
from be import *
from .be_subcmd import TestCommand


class NestedCommand(BeSubCommand, bapp.plugin_type()):
    """See if it works to have multiple nesting levels"""
    __slots__ = ()

    name = 'nested'
    version = '0.0.0'
    description = 'none'
    subcommands_title = 'sub-commands'


# end class NestedCommand


class NestedSubCommand(SubCommandBase, bapp.plugin_type()):
    """@todo documentation"""
    __slots__ = ()

    name = 'foo'
    version = '0.0.0'
    description = 'none'
    main_command_name = NestedCommand.name

    def execute(self):
        return self.SUCCESS

# end class NestedSubCommand


class TestCmd(BeTestCase):
    __slots__ = ()

    @with_application
    def test_base(self):
        cmd = BeCommand(bapp.main())
        assert cmd.parse_and_execute('foo'.split()) != 0, "command didn't exist"
        assert cmd.parse_and_execute([TestCommand.name]) == 0, "command did exist"


# end class TestCmd
