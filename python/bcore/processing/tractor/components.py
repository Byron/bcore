#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.components
@brief Implements interfaces in bcore.processing.tractor.interfaces

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorProcessDataProvider', 'TractorNodeGeneratorChainProvider']

import os

from .interfaces import (
                            ITractorProcessDataProvider,
                            ITractorNodeGeneratorChainProvider
                        )
from .alf.generators import (
                                TractorCmdGeneratorBase,
                            )
from .alf.generators import NodeGeneratorChainBase
from bcore.core.kvstore import KeyValueStoreProvider


class TractorProcessDataProvider(ITractorProcessDataProvider, Plugin):
    """Implements the data provider interface, works together with TractorDelegateMixin and TractorCmdGeneratorBase"""
    __slots__ = ()
    
    def data(self):
        evar = TractorCmdGeneratorBase.data_storage_env_var
        if evar not in os.environ:
            return None
        return TractorCmdGeneratorBase.deserialize_data(os.environ[evar])
        
    def set_progress(self, progress):
        print "TR_PROGRESS %03i%%"
        
    def as_kvstore(self):
        data = self.data()
        if data is None:
            return None
        return KeyValueStoreProvider(data)

# end class TractorProcessDataProvider


class TractorNodeGeneratorChainProvider(ITractorNodeGeneratorChainProvider, Plugin):
    """Provide nodes of the required type using services"""
    __slots__ = ()

    def chains(self):
        return new_services(NodeGeneratorChainBase)

# end class TractorNodeGeneratorChainProvider

