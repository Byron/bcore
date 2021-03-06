#-*-coding:utf-8-*-
"""
@package bapp.tests.bin.test_wrapper
@brief tests for bapp.bin.wrapper

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = []

import sys
import os.path

import bapp
from bapp import preserve_application
from butility.tests import TestCase
from butility import load_file

# Dynamic loading of wrapper code - its not in a package for good reason
dirname = os.path.dirname
wrapper_file = os.path.join(dirname(dirname(__file__)), 'bootstrap.py')
bootstrap = load_file(wrapper_file, 'bootstrap')
import bootstrap


class TestBootstrap(TestCase):

    """Tests for the bootstrap implementation"""
    __slots__ = ()

    @preserve_application
    def test_base(self):
        """test fundamentals
        @note doesn't run all code paths, but its just a few lines"""
        # Should be dealing with its executable being python as well as its file
        self.failUnlessRaises(SystemExit, bootstrap.Bootstrapper().main, wrapper_file)
        self.failUnlessRaises(AssertionError, bootstrap.Bootstrapper().main, '/some/nonesense')

        # this will actually do something (but not start a program)
        try:
            bootstrap.Bootstrapper().main(self.fixture_path('bin/foo'), '-file')
        except AssertionError:
            # expected, as it will complain about it not being a symlink
            pass
        # end handle exception


# end class TestWrapper
