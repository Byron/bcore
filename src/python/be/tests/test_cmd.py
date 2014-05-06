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
from be import *


class TestBeSubCommand(BeSubCommand, bapp.plugin_type()):
    """@todo documentation"""
    __slots__ = ()

    name = "hello"
    version = '0.0.0'
    description = "prints hello world"

    def execute(self, args, remaining_args):
        print "hello world"
        return self.SUCCESS

# end class TestBeSubCommand


class TestCmd(BeTestCase):
    __slots__ = ()

    @with_application(from_file=__file__)
    def test_base(self):
        cmd = BeCommand(bapp.main())
        assert cmd.parse_and_execute('foo'.split()) != 0, "command didn't exist"
        assert cmd.parse_and_execute([TestBeSubCommand.name]) == 0, "command did exist"


        configured_name = 'new-name'
        assert cmd.info_data().name == configured_name, \
                                                    "it's possible to rename a be command"

# end class TestCmd
