#-*-coding:utf-8-*-
"""
@package tx.tests.core.component.core
@brief Utilities used for testing the component system

@copyright 2012 Sebastian Thiel
"""
__all__ = ['TestComponentCoreBase', 'with_rw_directory']

# REVIEW: This seems to be partially a remnant of the pyutilib. Make sure to reassess what should remain here,
# and what needs to be removed.

import os
import sys
import re
import zipfile

from os.path import abspath, dirname

import bcore
from bcore.tests import (
                        TestCaseBase,
                        with_rw_directory
                     )

from bcore.core.component import *


# ==============================================================================
## @name Classes
# ------------------------------------------------------------------------------
## @{

class TestComponentCoreBase(TestCaseBase):
    __slots__ = ()

    # This regex is for recognizing float values, might be good to expand and put in utils.
    float_p = r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"

    _old_stdout = list()
    _old_stderr = list()
    _local_file = True

    def fixture_path(self, name):
        """@return a fixture path for component tests"""
        return super(TestComponentCoreBase, self).fixture_path('') / 'core' / 'component' / name


# end class TestComponentCoreBase


## -- End Classes -- @}

