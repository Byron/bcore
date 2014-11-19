#-*-coding:utf-8-*-
"""
@package bdiff.utility
@brief Utiltiies for use when diffing and merging is required

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = ['merge_data']


# ==============================================================================
# @name Routines
# ------------------------------------------------------------------------------
# @{

def merge_data(source, destination, delegate_type=None, diff_type=None):
    """A quick-and-dirty helper to more easily perform a merge operation, with all the object types involved
    @param delegate_type if None, it will default to AutoResolveAdditiveMergeDelegate
    @param diff_type if None, it defaults to TwoWayDiff
    @return the delegate's result of the merge operation"""
    # have to use delayed imports here, to mask the dependency which utility shouldn't really have
    if delegate_type is None:
        from .delegates import AutoResolveAdditiveMergeDelegate as delegate_type
    if diff_type is None:
        from .algorithms import TwoWayDiff as diff_type
    delegate = delegate_type()
    diff_type().diff(delegate, destination, source)
    return delegate.result()

# -- End Routines -- @}
