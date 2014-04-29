#-*-coding:utf-8-*-
"""
@package bcontext.tests.core
@brief Utilities used for testing the component system

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['TestContextBase']

from butility import Path
from butility.tests import TestCaseBase


# ==============================================================================
## @name Classes
# ------------------------------------------------------------------------------
## @{

class TestContextBase(TestCaseBase):
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

# end class TestContextBase

## -- End Classes -- @}

