#-*-coding:utf-8-*-
"""
@package bapp.schema
@brief All environment schemas used in the pipeline core

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
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
