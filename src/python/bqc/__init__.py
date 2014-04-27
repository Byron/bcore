#-*-coding:utf-8-*-
"""
@package bqc
@brief A framework to implement quality assurance on a very basic level.

@page qc Quality Assurance Framework

Before you can use the framework, you need to implement a `QualityCheck`. This is as simple as follows:
@snippet bapp/tests/doc/test_examples.py quality_check

Now you create a runner, initialize it with your quality checks, and run it. 
@snippet bapp/tests/doc/test_examples.py quality_check_usage

A delegate should be implemented in case you want more feedback and control.

@copyright 2012 Sebastian Thiel
"""
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

from .interfaces import *
from .base import *

