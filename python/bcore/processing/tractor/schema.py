#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.schema
@brief tractor-related schemas for general use

@copyright 2013 Sebastian Thiel
"""
__all__ = ['submitter_schema']

from bcore.core.kvstore import KeyValueStoreSchema

tractor_schema = KeyValueStoreSchema('tractor', { 'submission' : { 'priority' : dict( low = 0,
                                                                                         normal = 1,
                                                                                         high = 2 ) 
                                                                    },
                                                    'engine' :     { 'hostname' : str,
                                                                     'port' : int
                                                                   }
                                                   }
                                       )
