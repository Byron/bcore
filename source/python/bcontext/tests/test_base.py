#-*-coding:utf-8-*-
"""
@package bcontext.tests.test_base
@brief Test for bcontext.base

@copyright 2012 Sebastian Thiel
@todo get rid of the standard error redirect or maybe solve it differently
"""
__all__ = []

from butility import (InterfaceBase,
                      abstractmethod)

from .base import TestContextBase

from bcontext import *


class TestPlugin(TestContextBase):

    def test_todo(self):
        self.fail("Need to rewrite all tests")

    def test_loader(self):
        """Verify fundamental loader features"""
        module = PluginLoader.load_file(self.fixture_path('plugin.py'), 'test_plugin')
        assert module is not None and hasattr(module, 'MyDynamicPlugin')
        
        self.failUnlessRaises(AssertionError, PluginLoader.load_file, self.fixture_path('plugin_fail.py'), 'doesnt-matter')
        self.failUnlessRaises(IOError, PluginLoader.load_file, self.fixture_path('doesntexist.py'), 'doesnt-matter')

# end class TestPlugin
