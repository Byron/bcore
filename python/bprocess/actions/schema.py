#-*-coding:utf-8-*-
"""
@package bcore.processcontrol.actions.schema
@brief Contains schemas used in all actions we implement

@copyright 2013 Sebastian Thiel
"""
__all__ = ['action_schema']

from bcore.kvstore import (
                                KeyValueStoreSchema,
                                AnyKey,
                            )

from bcore.path import Path


action_schema = KeyValueStoreSchema('package-actions', {AnyKey : dict()})


