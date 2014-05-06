#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_plugins
@brief tests for bprocess.plugins

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import bapp
from bapp.tests import with_application
from butility.tests import TestCaseBase

# test import *
from bprocess.plugins.be_go import *


class PluginsTestCase(TestCaseBase):
    __slots__ = ()

    @with_application(from_file=__file__)
    def test_launcher(self):
        cmd = LauncherBeSubCommand(application=bapp.main())
        assert cmd.parse_and_execute([]) == 0, 'empty program will just list nothing'


# end class PluginsTestCase
