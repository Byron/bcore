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
from butility import PythonFileLoader

from bcontext import *


class TestPlugin(TestContextBase):

    def test_context(self):
        """Verify context methods"""
        

    def test_context_stack(self):
        """Verify context stack functionality"""
        

    def test_plugin(self):
        """verify plugin type registration works"""
        stack = ContextStack()
        MyPlugin = PluginMeta.new(stack)
        assert MyPlugin._stack is stack
        assert MyPlugin.__metaclass__._stack is stack

        class PluginType(MyPlugin):
            """A plugin, for our stack"""
            __slots__ = ('id')

            count = 0

            def __init__(self):
                self.id = self.count
                type(self).count += 1

        # end class PluginType

        assert len(stack.classes(PluginType)) == 1, "Expected to have caught type"
        assert not stack.services(PluginType), "There is no instance yet"

        # This would be a singleton
        for count in range(2):
            PluginType()
            instances = stack.services(PluginType)
            assert len(instances) == count+1, "There should be exactly %i instance(s)" % count
            assert instances[0].id == count, "First service should always be the latest created one"
        # end check instantiation and order

    def test_loader(self):
        """Verify fundamental loader features"""
        module = PythonFileLoader.load_file(self.fixture_path('plugin.py'), 'test_plugin')
        assert module is not None and hasattr(module, 'MyDynamicPlugin')
        
        self.failUnlessRaises(AssertionError, PythonFileLoader.load_file, self.fixture_path('plugin_fail.py'), 'doesnt-matter')
        self.failUnlessRaises(IOError, PythonFileLoader.load_file, self.fixture_path('doesntexist.py'), 'doesnt-matter')

# end class TestPlugin
