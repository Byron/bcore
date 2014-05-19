#-*-coding:utf-8-*-
"""
@package be.cmd
@brief contains the BeCommand implementation

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['BeCommand', 'BeSubCommand']

from bapp import ApplicationSettingsMixin
from bkvstore import KeyValueStoreSchema
from butility import Version
from bcmd import (Command,
                  SubCommand)


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

def _init_schema(key, clsdict):
    """Initialize our schema, the given key as root key.
    In case you derive from BeCommand, you might want to store your configuration elsewhere.
    @param key name of the root key at which to place settings, like 'be' , or 'foo'.
    @param clsdict your classes locals, call locals() from the body of your class
    @return the new schema, usually assigned to _schema class member"""
    return KeyValueStoreSchema('be', {   'name' : key,
                                         'version' : clsdict['version'],
                                         'description' : clsdict['description']})

## -- End Utilities -- @}



class BeCommand(Command, ApplicationSettingsMixin):
    """Marries the 'be' framework with the command framework"""
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{
    
    ## we are only called 'be' if this value is queried through the class, which nobody should be 
    ## doing anyway
    name = 'be'
    version = Version('0.1.0')
    description = "universal commandline tool"

    # make sure we have subcommand support
    subcommands_title = 'sub-commands'
    subcommands_description = 'a list of plugins providing additional functionality, each as own sub-command'
    
    ## -- End Configuration -- @}


    # NOTE: If your derived type overrides the name to get a different space in the kvstore, you need an
    # adjusted SubCommand.main_command
    _schema = _init_schema(name, locals())

    # -------------------------
    ## @name Overrides
    # @{

    def info_data(self):
        """Obtains the name and other information from the settings"""
        return self.settings_value(self.application().context().settings())
    
    ## -- End Overrides -- @}


# end class BeCommand


class BeSubCommand(SubCommand):
    """Your custom subcomand should derive from this type to facilitate becoming a be-subcommand 
    that will be loaded automatically.

    Additionally, derive form bapp.plugin_type().
    """
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{

    main_command = BeCommand

    ## -- End Configuration -- @}

    # -------------------------
    ## @name Subclass Interface
    # @{

    @classmethod
    def _main_command_name(cls):
        """@return the name of our main command"""
        return cls.main_command.settings_value().name
    
    ## -- End Subclass Interface -- @}

    def is_compatible(self, command):
        """@return We will always be compatible to the be-command, based on the configuration"""
        return command.info_data().name == self._main_command_name()

# end class BeSubCommand


if __name__ == '__main__':
    BeCommand.main()
