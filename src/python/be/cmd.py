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


class BeCommand(BeCommandMixin, CommandBase):
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

    _schema = KeyValueStoreSchema(name, {'name' : name})


# end class BeCommand


class BeSubCommand(SubCommandBase):
    """Your custom subcomand should derive from this type to facilitate becoming a be-subcommand 
    that will be loaded automatically.

    Additionally, derive form bapp.plugin_type()
    """
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{

    ## It's ok for use to refer to the be command (even though on the shell it might be named differently)
    # As all subcommands are loaded explicitly. This is to assure one BeSubCommand doesn't reach a 
    # a BeCommand it wasn't intended for
    main_command_name = BeCommand.name
    
    ## -- End Configuration -- @}

# end class BeSubCommand


if __name__ == '__main__':
    BeCommand.main()
