#-*-coding:utf-8-*-
"""
@package bcore.processcontrol.utility
@brief A collection of utilities to ease the work of controller and delegate

@copyright 2013 Sebastian Thiel
"""
__all__ = ['controller_schema', 'process_schema', 'package_schema', 'python_package_schema',
           'package_meta_data_schema']


import bcore
from bcore.log import module_logger
from bcore.component import CreateFirst
from bkvstore import (
                                KeyValueStoreSchema,
                                AnyKey,
                                StringList,
                                PathList
                            )
from .interfaces import IProcessControllerDelegate
from bcore import Version
from bcore.utility import LazyMixin
from butility import Path

log = module_logger('bcore.processcontrol.schema')

# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class NamedServiceProcessControllerDelegate(LazyMixin):
    """Utility type to create a delegate as a service from the given name.
    We use it as dynamic constructor"""
    __slots__ = ('instance', '_delegate_name')
    
    @classmethod
    def _type_matches_name(cls, name, svccls, *args):
        return CreateFirst(svccls, *args) and svccls.__name__ == name
    
    def __init__(self, delegate_name = None):
        """Fill our instance"""
        self._delegate_name = delegate_name
        
    def _set_cache_(self, name):
        if name == 'instance':
            self.instance = None
            if not self._delegate_name:
                return
            # end handle value unset
            
            delegates = bcore.environment.new_services(IProcessControllerDelegate, 
                                            predicate = lambda *args: self._type_matches_name(self._delegate_name, *args))
            if not delegates:
                raise AssertionError("Delegate named '%s' could not be found in service registry" % self._delegate_name)
            # handle delegate instantiation
            
            self.instance = delegates[0]
        else:
            super(NamedServiceProcessControllerDelegate, self)._set_cache_(name)
        # end handle cache
    

# end class NamedServiceProcessControllerDelegate

## -- End Utilities -- @}


process_schema = KeyValueStoreSchema('process', { 
                                                    # kvstore id of the program to run, usually the basename of the executable
                                                    'id' : str,
                                                    # Full path to the executable we were supposed to run
                                                    'executable' : Path,
                                                    # Directory containing the executable, i.e. dirname(executable)
                                                    # Useful for kvstore substitution
                                                    'bootstrap_dir' : Path,
                                                }
                                    )


package_schema = KeyValueStoreSchema(AnyKey,            # Path to the root of the package. All relative paths will be 
                                                        # made absolute with the first valid root path
                                                        { 'root_paths' : PathList,
                                                         # absolute or relative path to the executable    
                                                          'executable' : Path,
                                                          'legacy_inherit_env' : False,
                                                          # A list of paths to directories and files from which all python files should be loaded
                                                          'plugin_paths' : PathList,
                                                          # The python paths to set at wrap time
                                                          'python_paths' : PathList,
                                                          'import_modules' : StringList,
                                                          'version' : Version(),
                                                          # Path to the current working directory of the process
                                                          # This will not affect the current working dir set for 
                                                          # setting up the configuration
                                                          'cwd' : Path,
                                                          'vspec' : {
                                                              'major' : str,
                                                              'minor' : str,
                                                              'patch' : str,
                                                          },
                                                          # We are explicit about our delegate type, so this needs to be overridden
                                                          'delegate' : NamedServiceProcessControllerDelegate('ProcessControllerDelegate'),
                                                          'requires' : StringList,
                                                          # A list of packages not to consider in our requirements
                                                          # only used when building the process environment
                                                          'exclude' : StringList,
                                                          # An alias to the package which provides the executable of our program
                                                          'executable_alias' : str,
                                                          'arguments' : {
                                                              # Arguments to append
                                                              'append' : StringList,
                                                              # arguments to prepend
                                                              'prepend' : StringList
                                                          },
                                                          # tractor specific information
                                                          'environment' : {
                                                              'linker_search_paths' : PathList,
                                                              'executable_search_paths' : PathList,
                                                              # Environment Variables we are to set
                                                              'variables' : {
                                                                AnyKey : StringList
                                                              }
                                                           },
                                                        # a list of keys into the package actions
                                                        # Dictionary. It is accessed using a variable schema
                                                        # depending on the type of action.
                                                        # Specified using type.name
                                                        'actions' : StringList
                                                        }
                                                    )

## This doesn't need to be a schema, its used as building block to make one
python_package_schema = {
                               'requires' : package_schema.requires,
                               'version' : package_schema.version,
                               'vspec' : package_schema.vspec,
                               'root_paths': package_schema.root_paths,
                               'python' : {
                                    'import' : StringList,
                                    'plugin_paths' : PathList
                               }
                         }


## see python_package_schema
package_meta_data_schema = {
                                'requires' : package_schema.requires,
                                'name' : str,
                                'url' : str,
                                'description' : str,
                                'version': package_schema.version
                           }

package_vspec_schema = {
    'requires' : package_schema.requires,
    'name' : str,
    'vspec' : package_schema.vspec,
    'version': package_schema.version
}

controller_schema = KeyValueStoreSchema('packages', {  package_schema.key() : package_schema })

