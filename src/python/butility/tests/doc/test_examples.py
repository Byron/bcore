#-*-coding:utf-8-*-
"""
@package butility.tests.doc.test_examples

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import sys

import bapp
from butility.tests import (TestCaseBase,
                            with_rw_directory)

from butility import LazyMixin



# ==============================================================================
## \name TestTypes
# ------------------------------------------------------------------------------
# Types that derive from the type to be tested
## \{

## [LazyMixinExample Implementation]
class LazyMixinExample(LazyMixin):
    """Example for LazyMixin"""
    __slots__ = 'example' # this is the cached attribute - it will be filled on demand
    
    prefix = "Hello World"

    def _set_cache_(self, attr):
        """Fill our slot"""
        if attr == 'example':
            self.example = "%s - this is cached" % self.prefix
        else:
            return super(LazyMixinExample, self)._set_cache_(attr)
        #end handle attribute

# end class LazyMixinExample
## [LazyMixinExample Implementation]




class ExamplesTest(TestCaseBase):
    """Provides a space to test your own code examples"""
    __slots__ = ()

    ##[with_rw_directory]
    @with_rw_directory
    def test_rw_decorator(self, rw_dir):
        """example rw _directory decorator usage"""
        self.failUnless(rw_dir.isdir())
        (rw_dir / "somefile").touch()
    ##[with_rw_directory]
    
    def test_lazymixin_example(self):
        """verify the LazyMixinExample produces the value we expect"""
        ## [LazyMixinExample Example]
        attr = 'example'
        assert hasattr(LazyMixinExample(), attr)
        assert getattr(LazyMixinExample(), attr).startswith(LazyMixinExample.prefix)
        ## [LazyMixinExample Example]

# end class ExamplesTest
