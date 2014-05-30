#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_plugins
@brief tests for bprocess.plugins

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = []

import os

import bapp
from be import BeCommand
from bapp.tests import with_application
from butility.tests import TestCase
from butility import Path
from .test_base import pseudo_executable
from bprocess.controller import _ProcessControllerContext


class PluginsTestCase(TestCase):
    __slots__ = ()

    @with_application(from_file=__file__)
    def test_launcher(self):
        # This makes sure we can resolve the configuration file. It's internal use only !
        # test import *
        # Must be done here, otherwise we can 'loose' the plugin for our invocation due to 
        # changing Application states
        from bprocess.plugins.be_go import *
        go = LauncherBeSubCommand.name
        go_exec = pseudo_executable(go)
        bapp.main().context().push(_ProcessControllerContext(go, 
                                                             go_exec,
                                                             'doesntmatter', []))
        cmd = BeCommand(application=bapp.main()).parse_and_execute

        assert cmd([go]) == 0, 'empty program will just list executables'
        assert cmd([go, 'foo']) != 0, 'invalid names are an error'
        # We are lazy here - instead of launching it through ProcessController.execute_in_current_context()
        # we just set the CWD for it to pick up the correct configuration
        cwd = os.getcwd()
        try:
            os.chdir(go_exec.dirname())
            assert cmd([go] + '+spawn py-program'.split()) == 0, 'can launch programs that exist for him'
        finally:
            os.chdir(cwd)
        # end cwd handling



# end class PluginsTestCase
