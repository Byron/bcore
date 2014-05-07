#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_plugins
@brief tests for bprocess.plugins

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import bapp
from be import BeCommand
from bapp.tests import with_application
from butility.tests import TestCaseBase
from butility import Path
from .test_base import pseudo_executable

# test import *
from bprocess.plugins.be_go import *
from bprocess.controller import _ProcessControllerContext


class PluginsTestCase(TestCaseBase):
    __slots__ = ()

    @with_application(from_file=__file__)
    def test_launcher(self):
        # This makes sure we can resolve the configuration file. It's internal use only !
        go = LauncherBeSubCommand.name
        bapp.main().context().push(_ProcessControllerContext(go, 
                                                             pseudo_executable(go),
                                                             'doesntmatter', []))
        cmd = BeCommand(application=bapp.main()).parse_and_execute

        assert cmd([go]) == 0, 'empty program will just list executables'
        assert cmd([go, 'foo']) != 0, 'invalid names are an error'
        assert cmd([go] + '--spawn py-program'.split()) == 0, 'can launch programs that exist for him'



# end class PluginsTestCase
