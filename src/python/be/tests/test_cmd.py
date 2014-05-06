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
from .be_subcmd import TestCommand


class TestCmd(BeTestCase):
    __slots__ = ()

    @with_application
    def test_base(self):
        cmd = BeCommand(bapp.main())
        assert cmd.parse_and_execute('foo'.split()) != 0, "command didn't exist"
        assert cmd.parse_and_execute([TestCommand.name]) == 0, "command did exist"

        

# end class TestCmd
