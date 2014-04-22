#-*-coding:utf-8-*-
"""
@package bapp.schema
@brief All environment schemas used in the pipeline core

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from butility import Path
from bkvstore import (RootKey,
                      KeyValueStoreSchema )


platform_schema = KeyValueStoreSchema(RootKey, dict(
                                                    platform = { 'id' : 'unknown-platform' },
                                                    host = {'name' : str,
                                                            'fqname' : str},
                                                    user = {
                                                            # login name
                                                           'login' : str,
                                                           # home path
                                                           'home' : Path,
                                                    }
                                                ))

project_schema = KeyValueStoreSchema('project', { 'id' : str,
                                                  'paths' :    dict(
                                                                        source = Path,
                                                                        executables = Path,
                                                                        configuration = Path,
                                                                        output = Path
                                                                    )
                                                }
                                    )
