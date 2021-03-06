#-*-coding:utf-8-*-
"""
@package bcontext.tests.test_base
@brief Test for bcontext.base

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
@todo get rid of the standard error redirect or maybe solve it differently
"""
from __future__ import unicode_literals

from butility.future import str
__all__ = []

from butility import (Interface,
                      abstractmethod)

from .base import TestContext

from bkvstore import KeyValueStoreModifier
from bcontext import *


class TestPlugin(TestContext):

    def test_context(self):
        """Verify context methods"""
        ctx = Context('name')
        assert ctx.name() == 'name'

        assert not ctx.types(object)
        assert not ctx.instances(object)
        assert len(list(ctx.settings().keys())) == 0

        inst = ctx.register('foo')
        assert not ctx.types(str)
        assert len(ctx.instances(str)) == 1

        ctx.register(inst)
        assert len(ctx.instances(str)) == 1, "register should check for duplicates"

        assert ctx.instances(str)[0] is inst
        assert not ctx.reset().instances(str)

    def test_context_stack_types(self):
        """Verify context stack functionality"""
        stack = ContextStack()

        assert len(stack) == 0, "Should have no default Context"
        assert len(stack.stack()) == 0

        # an empty stack should provide nothing
        assert len(stack.instances(object)) == 0
        assert len(stack.types(object)) == 0
        assert len(list(stack.settings().keys())) == 0
        assert len(stack.new_instances(object)) == 0

        for until_size in (-1, 1):
            self.failUnlessRaises(ValueError, stack.pop, until_size)
        # end check error handling

        # String is converted to Context
        foo_context = stack.push('foo')
        bar_context = stack.push(Context('bar'))

        assert len(stack) == 2
        res = stack.pop(1)
        assert len(res) == 1
        assert res[0].name() == bar_context.name()

        # can't push same thing twice
        self.failUnlessRaises(ValueError, stack.push, foo_context)
        inst = 42
        stack.register(inst)

        assert stack.instances(int)[0] is inst
        assert len(stack.instances(int)) == 1
        inst2 = inst * 2
        stack.push(bar_context)
        stack.register(inst2)
        assert stack.instances(int)[0] is inst2
        assert len(stack.instances(int)) == 1

        res = stack.instances(int, find_all=True)
        assert len(res) == 2 and res[-1] is inst

        # forget last modification
        assert stack.pop() is bar_context
        assert stack.instances(int)[0] is inst

        assert stack.pop() is foo_context
        assert not stack.instances(int)

        # Test class instantiation
        stack.push(foo_context)
        stack.register(str)

        res = stack.new_instances(str, args=[5])
        assert len(res) == 1 and res[0] == '5'
        assert not stack.instances(str)

        # non-plugin instances can be kept as well
        stack.new_instances(str, args=[5], take_ownership=True)
        assert len(stack.instances(str)) == 1

    def test_stack_settings(self):
        """test settings aggregation"""
        kv1 = KeyValueStoreModifier({'one': {'one': 1,
                                             'two': 2},
                                     'two': 2})

        stack = ContextStack()
        ctx = Context('first')
        ctx.set_settings(kv1)
        stack.push(ctx)

        kv2 = KeyValueStoreModifier({'one': {'one': '1',
                                             'three': 3},
                                     'two': {'one': 1, 'foo': 2},
                                     'three': 3})

        assert stack.settings().data().to_dict() == kv1.data()

        ctx = Context('second')
        ctx.set_settings(kv2)
        stack.push(ctx)

        kvd = stack.settings().data()
        assert kvd.one.one == '1'
        assert kvd.one.three == 3
        assert kvd.one.two == 2
        assert kvd.three == 3
        assert kvd.two.one == 1

        # popping the previous context should bring the original one back
        stack.pop()
        kvd = stack.settings().data()
        assert kvd.to_dict() == kv1.data()

    def test_plugin(self):
        """verify plugin type registration works"""
        stack = ContextStack()
        stack.push('base')

        class MyPlugin(Plugin):

            """A plugin, for our stack"""
            __slots__ = ()
            _stack_ = stack

        # end class PluginType

        class PluginType(MyPlugin):
            __slots__ = ('id')

            count = 0

            def __init__(self):
                self.id = self.count
                type(self).count += 1

        # end class PluginType

        assert len(stack.types(PluginType)) == 1, "Expected to have caught type"
        assert not stack.instances(PluginType), "There is no instance yet"

        # context for instances
        stack.push('instances')

        # This would be a singleton
        for count in range(2):
            PluginType()
            instances = stack.instances(PluginType)
            assert len(instances) == count + 1, "There should be exactly %i instance(s)" % count
            assert instances[0].id == count, "First service should always be the latest created one"
        # end check instantiation and order

        # discard previous instances
        stack.pop()
        assert not stack.instances(PluginType), 'previous instances should have been discarded with the context'

        stack.push('new-instances')
        assert len(stack.new_instances(PluginType)) == 1, "A single new instance was created"
        assert not stack.instances(PluginType)

        res = stack.new_instances(PluginType, take_ownership=True)
        assert len(res) == 1
        assert stack.instances(PluginType) == res, "new instance should have been kept in context"

# end class TestPlugin
