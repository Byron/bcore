#-*-coding:utf-8-*-
"""
@package submodule
@brief For runtime loading

@copyright 2014 Sebastian Thiel
"""
__all__ = []


class Bar(object):
    """Implements nothing"""
    __slots__ = ()

    @classmethod
    def foo(cls):
        return 'bar'

# end class Foo
