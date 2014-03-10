#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.generators.maya_entrypoint
@brief Startup whatever tractor provded to us

@copyright 2013 Sebastian Thiel
"""
__all__ = []

import bcore
log = service(bcore.ILog).new('bcore.processing.tractor.alf.generators.maya_entrypoint')

from .maya import MayaBatchTaskGenerator


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

def run():
    """run the tractor-provided script"""
    provider = new_service(bcore.ITractorProcessDataProvider)
    store = provider.as_kvstore()
    assert store is not None, "Must be executed via tractor and receive contextual data - don't now what to run"
    
    data = store.value(MayaBatchTaskGenerator.static_field_schema.key(), MayaBatchTaskGenerator.static_field_schema)
    
    # The evaluated string has access to our data and store
    ######################
    log.info(data.cmd.python)
    exec(data.cmd.python)
    ######################
    
## -- End Utilities -- @}

