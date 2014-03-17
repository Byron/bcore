#-*-coding:utf-8-*-
"""
@package bcore.diff.utility
@brief Utiltiies for use when diffing and merging is required

@copyright 2013 Sebastian Thiel
"""
__all__ = ['merge_data']

from .algorithms import TwoWayDiff
from .delegates import AutoResolveAdditiveMergeDelegate


# ==============================================================================
## @name Routines
# ------------------------------------------------------------------------------
## @{

def merge_data(source, destination, delegate_type = AutoResolveAdditiveMergeDelegate, diff_type = TwoWayDiff):
    """brief docs"""
    delegate = delegate_type()
    diff_type().diff(delegate, destination, source)
    return delegate.result()
    

## -- End Routines -- @}



