#-*-coding:utf-8-*-
"""
@package be.cmd
@brief contains the BeCommand implementation

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['BeCommand', 'BeCommandMixin', 'BeSubCommand']

from bapp import ApplicationSettingsClient
from bkvstore import KeyValueStoreSchema
from butility import Version
from bcmd import (CommandBase,
                  SubCommandBase)


class BeCommandMixin(object):
    """A mixin for use in a CommandBase compatible type.

    It implements all the functionality of the 'be' command framework.
    """
    __slots__ = ()


# end class BeCommandMixin


class BeCommand(BeCommandMixin, CommandBase, ApplicationSettingsClient):
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

    # NOTE: we must have a fixed entry point into the configuration ! It's always 'be'
    _schema = KeyValueStoreSchema('be', {'name' : name,
                                         'version' : version,
                                         'description' : description})

    # -------------------------
    ## @name Overrides
    # @{

    def info_data(self):
        """Obtains the name and other information from the settings"""
        return self.settings_value(self.application().context().settings())
    
    ## -- End Overrides -- @}


# end class BeCommand


class BeSubCommand(SubCommandBase):
    """Your custom subcomand should derive from this type to facilitate becoming a be-subcommand 
    that will be loaded automatically.

    Additionally, derive form bapp.plugin_type().
    """
    __slots__ = ()


    def is_compatible(self, command):
        """@return We will always be compatible to the be-command, based on the configuration"""
        return command.info_data().name == BeCommand.settings_value().name

# end class BeSubCommand


if __name__ == '__main__':
    BeCommand.main()
