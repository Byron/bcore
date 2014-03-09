#-*-coding:utf-8-*-
"""
@package tx

@mainpage Overview

@section core Core Frameworks

- @subpage logging
- @subpage components
- @subpage diff
- @subpage kvstore
- @subpage processcontrol
- @subpage qc
- @subpage interfaces
- @subpage commands
- @subpage tractor_alf


@section new What's New

## What's new in 0.9.0

- TBA

## What's new in 0.8.0

- **Process Control**
 + **Package Actions**
  -  Even though it was possible for root-packages to have custom delegates, it wasn't easily possible to attach
    custom behaviour to normal packages.
  - Actions are living under the 'package-actions.[type].[name]' key in the kvstore and can use an individual 
    schema per action type.
  -  Actions are operations that are part of a transaction. This makes sure that failed actions will cause 
    previous successful actions to be rolled back properly, to prevent leaving the system in an inconsistent state.
 + **Package Exclusion**
  - Package data now supports the 'exclude' keyword, which marks a package that should in no case be loaded. This 
    is useful if you want to replace one package with another one. It is important to assure the exclude keyword
    occurs before the package that is supposed to be excluded.
- **Tractor RPC**
 + You can now connect to a blade and the tractor engine to submit rpc commands.
 + Read more about the TractorConnection and its derivatives

## What's new in 0.7.0

- **Properties Core Framework**
 + Added a framework to unify descriptor based property handling, see \ref tx.core.properties
- **Addition to \ref components "Component Framework"**
 + Properties are provided to simplify access to context values using Properties.
 + See \ref tx.core.component.properties for more information
- **Logging**
 + The logging initialization will now work as expected when initialized from a file. Previously 
   it would make all existing logger instances unusable.
 + TX_LOGGING_INITIALIZATION_DISABLE can be set to prevent any logging initialization. It is the 
   same as if the kvstore contained the logging.disable=1 flag, but is more granular as the 
   environment can more easily be manipulated per process.
- **ProcessControl**
 + Great speed improvements - the new version of the wrapper is about 60% faster, on windows this will be
   very noticeable, but even on linux it is a considerable improvement.
 + Fixed possible issue on windows which could end up without kvstore if it grew above the size of 32kb
 + Moved everything to a point where bcore will not work as expected (due to missing kvstore data) 
   if used unwrapped and if no one else is setting up the environment accordingly.
 + Added 'python_paths' option, which allows to set the PYTHONPATH at wrap time. That way, 'import_modules' 
   can be used easily. Main benefit is that delegates can use an actual package structure and absolute imports,
   which is not possible if the module was just executed.
 + Improved debugging output to be more readable and more useful
 + Configuration string values can now be suffixed with an exclamation mark to prevent them from being overriden.
   This is especially useful with package versions.

## What's new in 0.6.0

- **New Types**
 + PersistentSettings - store changes to a dataset in a file
 + PersistentSettingsEnvironmentStackContextClient - load settings from a combination of changes and what's
   coming from the central kvstore. Allows us to make good presets per show for instance, and individuals 
   to make overrides.
 + PackageMetaDataChangeTracker - A utility type for tracking the state of a processing previous package
   configuration and to query the difference to the current one.
    - To feed it with data, all packages have received meta-data describing them further
- **New Widgets**
 + PackageViewerWidget
   - A widget using the PackageMetaDataChangeTracker to display information about changed packages 
     to the user.


## What's new in 0.5.0

- New Widgets
 + PluginSelectorWidget
- New Interfaces
 + IDirectoryServices
 + IProjectService
 + ISiteService
- Renamed *Services to *Service, which is relevant only for interfaces
- Plugin class now supports a minimal interface to provide information about it
- Pipeline support for specifying which additional modules to import on per-package level
 + Super-useful for configurable plugin loading
 + Examples for configuration.yaml
  + packages.name.python.import = [module, package.module] 
  + packages.name.python.plugin_paths = [relative/path/with/pyfiles, /absolute/path]
- Process Control
 + Added 'import_modules' directive to package configuration to allow importing modules in addition
   to loading any kind of plug-in
- Distributed **hostapps** package into their respective engines
- Fixes
 + Commandline Overrides are now carried over into the process. Previously, if you would change the version
   of a package using the commandline, the called process wouldn't know juding from its kvstore alone.

## What's new in 0.4.0

- Added \ref tx.processing.tractor "Tractor API"
 + This includes a module to build \ref tx.processing.tractor.alf "alf structures" and serialize them
- Added TX_STARTUP_LOG_LEVEL environment variable, which allows to set the log level very early on. Valid
  values are DEBUG or INFO for instance, namely log level constants available in the logging package.

## What's new in 0.3.0

- Added TRACE logging level. Use it like log.log(logging.TRACE, msg). Its right between INFO and DEBUG
- Process Control
 + ProcessControll delegate will now parse ---argument flags. Try ---help on your next invocation.
 + IProcessController interface removed, as the standard implementation is the ProcessController
 + ProcessController now needs an explicit .inti() call for initialization
 + Adde ProcessController.execute_in_current_context() method to facilitate in-process usage
- KVStore
 + *Changed default behaviour* - values which are not known to the schema will now by default NOT
   be returned anymore. If you want the previous behavior, use the a KeyValueStoreModifier with a 
   DiffProviderDelegateType being a RelaxedKeyValueStoreProviderDiffDelegate.
 + Unchecked access without a schema is intentionally hard to do, as it is not supposed to be used by default.
- New Interface: IContextControl
 + An interface to help tracking the executable and scene context.
 + Hostapps Maya now provides a MayaEnvironment to automatically setup most important components, such as 
   ContextTracking.
- GUI Package reorganized
 + Previously it contained Quality Checking related interfaces. Now its reserved for general purpose widgets
   that can be used to build larger user interfaces.
 + Quality Checking GUI was moved into tx.qc.gui.
- Standalone Quality Checking
 + in mainline/bin you will find a standalone version of the quality checker gui. If opened in the appropriate
   context, checks will show up, for instance to check file paths and naming.
- Batchman as standalone tool
 + Configuration was added to process control to allow starting batchman in standalone mode. It will need
   some more work though to reach that goal, but its very doable.

## What's new in 0.2.0

- \ref tx.db.shotgun.interfaces.IShotgunConnection "IShotgunConnection"
- \ref tx.db.shotgun.base.ProxyShotgunConnection "ProxyShotgunConnection"
- \ref tx.core.logging.interfaces.ILog "ILog"
- \ref tx.processcontrol "Process Control Improvements"
  + Added process.executable key to kvstore
  + Package Schema Additions
    * Added arguments.append and arguments.prepend keys to allow appending and prepending arguments
    * Added executable_alias to allow using the executable of another package.
- Moved all core interfaces into their respective package's interfaces module, therefore tx.core.interfaces
  is no more.
- Added new \ref commands "Command Framework"
  

## What's new in 0.1.0

- First stable release 

@page interfaces Core Interfaces

Interfaces are the preferred way to obtain functionality from the \ref components "components framework".

As they are so important, all interfaces defined here are automatically available in the tx package. 
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

# C0103 environ is an invalid module variable name, shold be constant. However, its desired in our case
# pylint: disable-msg=C0103

# ==============================================================================
## \name Globals
# ------------------------------------------------------------------------------
# All variables listed here are singleton instance which are useful to everyone
# within the tx package.
## \{

## allows access to the current context.
environment = None

## Used to set the logging up very early to see everything. Useful for debugging usually, log-levels will 
## be set at later points as well
log_env_var = 'TX_STARTUP_LOG_LEVEL'

## If set, we will perform only the most minimal (and the fastest possible) startup
minimal_init_evar = 'TX_INIT_ENVIRONMENT_DISABLE'

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

def _init_core():
    """Just import the core and let it do the rest"""
    from . import core
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
    core.initialize()
    
def init_environment_stack():
    """setup our global environment"""
    import bcore.core.component
    global environment
    environment = tx.core.component.EnvironmentStack()

    from bcore.core.environ import (OSEnvironment, PipelineBaseEnvironment)

    # Basic interfaces that we always need - everything relies on those values
    environment.push(OSEnvironment('os'))

def _init_logging():
    """Make sure most basic logging is available"""
    import bcore.core.logging
    tx.core.logging.initialize()

    # Make sure one instance of the provider is there, but don't initialize it (which loads configuration)
    # A lot of code expects it to be there
    from bcore.core.logging.components import LogProvider
    LogProvider()

    
def  init_environment():
    """Intializes processcontrol related environments, and our logging configuration
    @note techinically, processcontroll would now have to move into tx.core as we are using it during startup.
    Alternatively, we just provide a function and engines initialize it as they see fit ! Therefore we don't
    touch process control here, but provide functionality others can call if they need it. For now, we just
    do it for the callers convenience.
    @todo consider moving processcontrol into bcore, as the rule would require it. Imports in tx have to be
    from core, otherwise it must be loaded on demand"""
    from bcore.processcontrol import (
                                        ControlledProcessEnvironment,
                                        PythonPackageIterator
                                  )

    proc_env = ControlledProcessEnvironment()
    if proc_env.has_data():
        environment.push(proc_env)

        # Initialize basic logging, and load configuration
        from bcore.core.logging.components import LogProvider
        LogProvider.initialize()

        # Now import modules and add basic interface
        # NOTE: If someone doesn't want that, he can set the respective environment 
        # variable. People might want to delay plugin loading, or call this function themselves
        # For now, we leave it to reduce burden on engine level
        PythonPackageIterator().import_modules()
    # end handle accelerated module initialization
    
## -- End Initialization Handlers -- @}


def _initialize():
    """Initialize the tx package."""
    _verify_prerequisites()
    _init_core()
    init_environment_stack()
    _init_logging()

    if minimal_init_evar not in os.environ:
        init_environment()
    # end skip initialization of environment if necessary
    


# auto-initialize the main package !
_initialize()
