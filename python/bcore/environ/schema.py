#-*-coding:utf-8-*-
"""
@package bcore.environ.schema
@brief All environment schemas used in the pipeline core

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from bcore.path import Path
from bkvstore import (
                                RootKey, 
                                KeyValueStoreSchema
                             )


site_schema = KeyValueStoreSchema('site', { 'id' :  str,      # name of the site
                                            'root_path' : { 
                                                            'repository' : Path,
                                                            'configuration' : Path,
                                                            'software' : Path,
                                                            'executables' : Path,
                                                            'core' : Path,
                                                            'projects' : Path 
                                                          }
                                          }
                                )

platform_schema = KeyValueStoreSchema(RootKey, dict(
                                                    platform = { 'id' : 'unknown-platform' },
                                                    host = {'name' : str,
                                                            'fqname' : str},
                                                    user = {
                                                            # login name
                                                           'login' : str,
                                                           # home path
                                                           'home' : Path
                                                    }
                                                ))

project_schema = KeyValueStoreSchema('project', { 'id' : str,
                                                  'directory' : dict(
                                                                        source = Path,
                                                                        executables = Path,
                                                                        configuration = Path,
                                                                        output = Path
                                                                    )
                                                }
                                    )
