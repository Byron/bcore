#-*-coding:utf-8-*-
"""
@package module
@brief For runtime loading

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []


class Foo:
    """Implements nothing"""
    __slots__ = ()

    @classmethod
    def hello(cls):
        return 'world'

# end class Foo
