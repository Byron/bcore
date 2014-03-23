#-*-coding:utf-8-*-
"""
@package module
@brief For runtime loading

@copyright 2014 Sebastian Thiel
"""
__all__ = []



class Foo(object):
    """Implements nothing"""
    __slots__ = ()

    @classmethod
    def hello(cls):
        return 'world'

# end class Foo
