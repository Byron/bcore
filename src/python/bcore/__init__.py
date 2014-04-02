#-*-coding:utf-8-*-
"""
@package bcore

@mainpage Overview

@section core Core Framework

- @subpage components
- @subpage diff
- @subpage kvstore
- @subpage processcontrol

@section new What's New

## What's new in 0.1.0

- First stable release 

@page interfaces Core Interfaces

Interfaces are the preferred way to obtain functionality from the \ref components "components framework".

As they are so important, all interfaces defined here are automatically available in the bcore package. 
See the following example for reference.

@snippet bcore/tests/doc/test_examples.py interface_builtin

@copyright 2012 Sebastian Thiel
"""
# Allow better imports !
from __future__ import absolute_import

import os
import sys
import ConfigParser
import logging

from butility import Version
from .base import *

__version__ = Version('0.1.0')


# ==============================================================================
## \name Constants
# ------------------------------------------------------------------------------
## \{

## Used to set the logging up very early to see everything. Useful for debugging usually, log-levels will 
## be set at later points as well
log_env_var = 'BCORE_STARTUP_LOG_LEVEL'

## -- End Constants -- @}


# -------------------------
## @name Interface
# @{

def app():
    """@return currently initialized global app instance. See 
    @throws EnvironmentError if it wasn't yet initialized"""
    if Application.main is None:
        raise EnvironmentError("Application instance not yet initialized - call bcore.Application.new()")
    # end assert application was setup
    return Application.main

def plugin_type():
    """@return a PluginType which is a suitable base for your Plugin, which will be part of the 
    application context.
    @note this method should be used preferably as it will also work if there is no Application instance yet.
    Your type will be stored in a temoprary registry, and transferred to the final one when the first Application 
    is instantiated.
    """
    return Application.main and Application.main.Plugin or Application.Plugin
    

## -- End Interface -- @}



# ==============================================================================
## @name Initialization Handlers
# ------------------------------------------------------------------------------
# Specialized functions to initialize part of the bcore package
## @{


def _init_pre_app_loggig():
    """Allow early logging, prior to having an Application"""
    log_level = os.environ.get(log_env_var)
    if log_level is not None:
        logging.basicConfig()
        try:
            logging.root.setLevel(getattr(logging, log_level))
        except AttributeError:
            msg = "%s needs to be set to a valid log level, like DEBUG, INFO, WARNING, got '%s'" % (log_env_var, log_level)
            raise AssertionError(msg)
        #end handle early log-level setup
    # end have env var

## -- End Initialization Handlers -- @}


def _initialize():
    """Initialize the bcore package."""
    _init_pre_app_loggig()

    

_initialize()
