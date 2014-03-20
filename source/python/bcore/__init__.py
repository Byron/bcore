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

from bcore.base import *

__version__ = Version('0.1.0')


# C0103 environ is an invalid module variable name, shold be constant. However, its desired in our case
# pylint: disable-msg=C0103

# ==============================================================================
## \name Globals
# ------------------------------------------------------------------------------
# All variables listed here are singleton instance which are useful to everyone
# within the bcore package.
## \{

## allows access to the current context.
environment = None

## Used to set the logging up very early to see everything. Useful for debugging usually, log-levels will 
## be set at later points as well
log_env_var = 'BCORE_STARTUP_LOG_LEVEL'

## If set, we will perform only the most minimal (and the fastest possible) startup
minimal_init_evar = 'BCORE_INIT_ENVIRONMENT_DISABLE'

## -- End Globals -- @}



# ==============================================================================
## @name Initialization Handlers
# ------------------------------------------------------------------------------
# Specialized functions to initialize part of the bcore package
## @{

def _verify_prerequisites():
    """Assure we are running in a suitable environment"""
    min_version = (2, 6)
    if sys.version_info[:2] < min_version:
        raise AssertionError("Require python version of at least %i.%i" % min_version)
    #end if sys.version_info[:2] < min_version

def _init_component_framework():
    """Assure the component framework is available"""
    from . import component
    component.initialize()

def _init_core():
    """Just import the core and let it do the rest"""
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
    _init_component_framework()
    
def init_environment_stack():
    """setup our global environment"""
    import bcore.component
    global environment
    environment = bcore.component.EnvironmentStack()

    from bcore.environ import (OSEnvironment, PipelineBaseEnvironment)

    # Basic interfaces that we always need - everything relies on those values
    environment.push(OSEnvironment('os'))

def _init_logging():
    """Make sure most basic logging is available"""
    from . import log
    log.initialize()

    # Make sure one instance of the provider is there, but don't initialize it (which loads configuration)
    # A lot of code expects it to be there
    from .log.components import LogProvider
    LogProvider()

    
def  init_environment():
    """Intializes processcontrol related environments, and our logging configuration
    @note techinically, processcontroll would now have to move into bcore as we are using it during startup.
    Alternatively, we just provide a function and engines initialize it as they see fit ! Therefore we don't
    touch process control here, but provide functionality others can call if they need it. For now, we just
    do it for the callers convenience.
    @todo consider moving processcontrol into bcore, as the rule would require it. Imports in bcore have to be
    from core, otherwise it must be loaded on demand"""
    from bcore.processcontrol import (
                                        ControlledProcessEnvironment,
                                        PythonPackageIterator
                                  )

    proc_env = ControlledProcessEnvironment()
    if proc_env.has_data():
        environment.push(proc_env)

        # Initialize basic logging, and load configuration
        from .log.components import LogProvider
        LogProvider.initialize()

        # Now import modules and add basic interface
        # NOTE: If someone doesn't want that, he can set the respective environment 
        # variable. People might want to delay plugin loading, or call this function themselves
        # For now, we leave it to reduce burden on engine level
        PythonPackageIterator().import_modules()
    # end handle accelerated module initialization
    
## -- End Initialization Handlers -- @}


def _initialize():
    """Initialize the bcore package."""
    _verify_prerequisites()
    _init_core()
    init_environment_stack()
    _init_logging()

    if minimal_init_evar not in os.environ:
        init_environment()
    # end skip initialization of environment if necessary
    


# auto-initialize the main package !
_initialize()
