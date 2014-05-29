#-*-coding:utf-8-*-
"""
@package submodule
@brief For runtime loading

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from future.builtins import object
__all__ = []


class Bar(object):
    """Implements nothing"""
    __slots__ = ()

    @classmethod
    def foo(cls):
        return 'bar'

# end class Foo
