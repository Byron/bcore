#-*-coding:utf-8-*-
"""
@package bcontext.tests.core
@brief Utilities used for testing the component system

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['TestContext']

from butility import Path
from butility.tests import TestCase


# ==============================================================================
## @name Classes
# ------------------------------------------------------------------------------
## @{

class TestContext(TestCase):
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

# end class TestContext

## -- End Classes -- @}

