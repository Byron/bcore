#-*-coding:utf-8-*-
"""
@package bcmd.base
@brief Base implementations of the command interfaces

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['CommandBase', 'SubCommandBase', 'InputError']

import sys
import logging


import bapp
from butility import (LazyMixin,
                      DictObject)
from bprocess import ProcessAwareApplication

from .argparse import ( ArgumentError,
                        ArgumentTypeError,
                        ParserError )
from .interfaces import ( ICommand,
                          ISubCommand )
from .utility import ( CommandArgumentParser,
                       ArgparserHandledCall)


class InputError(Exception):
    """Thrown if one of the inputs to the commands turned out to be invalid"""
    __slots__ = ()
    

# end class InputError


class CommandBase(ICommand, LazyMixin):
    """Implements a simple command which is easily configured through overridable class members.
    
    It has built-in support for plugin-subcommands
    """
    __slots__ = (
                    '_log',         # our logging instance, lazy
                    '_info',        # info kv store, lazy
                    '_app',         # the application to use when querying the registry, or settings
                    '_level'        # the depth within the sub-command chain
                )
    
    ArgumentParserType = CommandArgumentParser 
    
    # -------------------------
    ## @name Information
    # Subclasses should override those values
    # @{
    
    ## Name of our program
    name = None
    ## A version string
    version = None
    ## Logging prefix, may be None
    log_id = None
    ## command description
    description = None
    
    ## If True, unknown or remaining arguments are allowed.
    ## This can be useful for variable argument list parsing.
    ## However, sometimes its just typos which lead to this, causing unexpected behaviour if incought
    allow_unknown_args = False

    ## -- End Information -- @}
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## If not None, a title to be used for the subcommand description
    ## It will also enable subcommand search.
    subcommands_title = None
    
    ## The description to be used for all subcommands
    ## If not None, it will also enable subcommand search
    subcommands_description = None
    
    ## Help for all found subcommands
    ## If not None, it will also enable subcommand search 
    subcommands_help = None

    ## If not None, and if no application instance is provided during initialization, we will create a default one
    # when instantiated.
    # Set this to the application type you want to intantiate, most commonly
    # If you want to override arguments, provide your own type and re-implement `new()`
    ApplicationType = ProcessAwareApplication

    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Constants
    # @{
    
    ## A constant to indicate success of our command. Useful as return value of the execute() method
    SUCCESS = 0
    
    ## A constant indicating a general error
    ERROR = 1
    
    ## A constant indicating an error related to file-io or accessibility
    FILE_ERROR = 2
    
    ## A constant indicating an error with argument parsing or handling
    ARGUMENT_ERROR = 3
    
    ## A constant indicating signal 15/SIGTERM, keyboard interrupt with Ctrl+C
    KEYBOARD_INTERRUPT = 4
    
    ## A constant indicating that the argument was handled by the argument parser itself, usually for 
    # low-level built-in flags
    ARGUMENT_HANDLED = 5
    
    ## A constant indicating an unhandled exception, which is usually a programming bug
    UNHANDLED_ERROR = 255
    
    ## -- End Constants -- @}

    def __init__(self, application=None):
        """Initialize this instance
        @param application instance of type Application, which is used to query the plugin registry. 
        If None, the global instance will be used automatically"""
        super(ICommand, self).__init__()
        self._app = application
        self._level = 0
        if self._app is None and self.ApplicationType:
            self._app = self.ApplicationType.new()
        # end 
    
    def _set_cache_(self, name):
        if name == '_log':
            lid = self.log_id or self.name
            if self._is_subcommand():
                lid = '%s %s' % (self.main_command_name, self.name)
            # end handle subcommands
            self._log = logging.getLogger(lid)
        elif name == '_info':
            assert self.name and self.version and self.description
            log_id = self.log_id or self.name
            self._info = DictObject(              {
                                                    'name' : self.name,
                                                    'version' : self.version,
                                                    'log_id' : log_id,
                                                    'description' : self.description
                                                  })
        else:
            return super(CommandBase, self)._set_cache_(name)
        # end handle name
        
    def _has_subcommands(self):
        """@return True if we have subcommands"""
        return any((self.subcommands_title, self.subcommands_description, self.subcommands_help))
       
    def _is_subcommand(self):
        """@return True if we are a subcommand"""
        return hasattr(self, 'main_command_name') and self.main_command_name

    def _subcommand_slot_name(self, level = None):
        """@return a name to access the args namespace, matching our level.
        That way, arbitrary depth command hierachies can be supported
        @param level if None, self._level will be used"""
        if level is None:
            level = self._level
        # end 
        return "__subcommand__%i" % level
        
    # -------------------------
    ## @name Interface Implementation
    # @{
    
    def info_data(self):
        return self._info
    
    def log(self):
        return self._log
        
    def setup_argparser(self, parser):
        """Default implementation adds nothing. This is common if you use subcommands primarily"""
        return self
        
    def execute(self, args, remaining_args):
        """Base implementation will just execute the selected subcommand
        @throws NotImplementedError if this command has no subcommands"""
        if not self._has_subcommands():
            raise NotImplementedError("Have no subcommands, thus the subclass needs to implement this")

        cmd = getattr(args, self._subcommand_slot_name())
        assert cmd is not self
        return cmd.execute(args, remaining_args)
            
        
    ## -- End Interface Implementation -- @}        
    # -------------------------

    ## @name Subclass Methods
    # Methods that can be overridden by subclasses
    # @{
    
    def _find_compatible_subcommands(self):
        """@return a list or tuple of compatible ISubCommand instances. Must contain at least one subcommand instance
        @note the base implementation searches the current environment stack for it"""
        return [scmd for scmd in (self.application() or bapp.main()).context().new_instances(ISubCommand) 
                                                                    if scmd.is_compatible(self)]
        
    def _add_version_argument(self, parser, version):
        """Set the given version as argument to the argparser.
        By default, we set the --version flag only, but subclasses can decide how they wish
        to handle it themselves
        @param parser an argparse.ArgumentParser instance
        @param version a version string"""
        parser.add_argument('--version', action='version', version=version)
    
    ## -- End Subclass Methods -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def argparser(self, parser = None):
        """@return a fully initialized arg-parser instance, ready for parsing arguments
        @param parser if set, you are called as neseted subcomand. Parser was initialized for you and 
        should be altered with your subcommands accordingly."""
        info = self.info_data()
        if parser is None:
            parser = self.ArgumentParserType(prog=info.name,
                                             description=info.description)

        # end handle parser
        self._add_version_argument(parser, str(info.version))
        self.setup_argparser(parser)
        if self._has_subcommands():
            subcommands = self._find_compatible_subcommands()
            if subcommands:            
                scmds_dict = dict()
                if self.subcommands_title:
                    scmds_dict['title'] = self.subcommands_title
                if self.subcommands_description:
                    scmds_dict['description'] = self.subcommands_description
                if self.subcommands_help:
                    scmds_dict['help'] = self.subcommands_help
                
                subparsers = parser.add_subparsers(**scmds_dict)
                for cmd in subcommands:
                    cmd_info = cmd.info_data()
                    subparser = subparsers.add_parser(cmd_info.name, description=cmd_info.description, help=cmd_info.description)
                    subparser.set_defaults(**{self._subcommand_slot_name() : cmd})
                    # Allow recursion - there can be a hierarchy of subcommands
                    assert cmd is not self, 'picked up myself as subcommand - check your name'
                    if cmd._has_subcommands():
                        # that way, the new subcommand master will be able to 
                        cmd._level = self._level + 1
                        cmd.argparser(subparser)
                    else:
                        cmd.setup_argparser(subparser)
                    # end handle arg initialization
                # end for each subcommand
            else:
                self.log().warn("Couldn't find a single subcommand")
            # end have subcommands
        # end handle subcommands
        return parser
        
    def parse_and_execute(self, args=None):
        """Parses the given argument list and executes the command.
        @note will catch exceptions and translates them into exit codes and logging output
        @param args tuple or list of argument strings. e.g. sys.argv[1:]. If None, sys.argv[1:0] is used automatically
        @return exit code as integer between 0 and 255. If an unhandled exception occurred, 255 will be returned
        @note If we implement subcommands, giving no arguments will print usage information and set an error code
        """
        if args is None:
            args = sys.argv[1:]
        # end handle args default
        
        parser = self.argparser()
        try:
            if self._has_subcommands() and not args: 
                parser.print_usage()
                return self.ERROR
            # print usage if nothing was specified
            parsed_args, remaining_args = parser.parse_known_args(args)
            if remaining_args:
                # traverse the subcommand chain and check if the last one actually allows unknown args
                level = self._level
                cmd = self
                unknown_allowed = False
                while cmd and not unknown_allowed:
                    cmd = getattr(parsed_args, self._subcommand_slot_name(level), None)
                    unknown_allowed |= cmd and cmd.allow_unknown_args or False
                    level += 1
                # end while there is no one to allow unknowns

                if not unknown_allowed:
                    sys.stderr.write("The following arguments could not be parsed: '%s'\n" % ' '.join(remaining_args))
                    return self.ERROR
                # end abort if no one allowed them
            # end handle remaining
            return self.execute(parsed_args, remaining_args)
        except ArgparserHandledCall, info:
            # Happens on help or version - exit with error anyway as we didn't do anything useful
            if info.message:
                sys.stdout.write(info.message + '/n')
            return self.ARGUMENT_HANDLED
        except ParserError, err:
            self.log().error(str(err))
            return self.ARGUMENT_ERROR
        except InputError, err:
            cmd = getattr(parsed_args, self._subcommand_slot_name(), None)
            (cmd and cmd.log() or self.log()).error(str(err))
            return self.ARGUMENT_ERROR
        except (ArgumentError, ArgumentTypeError), err:
            parser.print_usage(sys.stderr)
            self.log().error(str(err))
            return self.ARGUMENT_ERROR
        except KeyboardInterrupt:
            # Signal 15, or Ctrl+C
            self.log().error("Interrupted by user")
            return self.KEYBOARD_INTERRUPT
        except Exception, err:
            self.log().error("An unhandled exception occurred", exc_info=True)
            return self.UNHANDLED_ERROR
        # end exception handling
        
    @classmethod
    def main(cls):
        """Convenience method to instantiate this type and run its parse_and_execute().
        It will also perform a system-exit with the exit code of the exit code of the aforementioned method"""
        sys.exit(cls().parse_and_execute())

    def application(self):
        """@return the Application instance we should use for plugin queries, or None if it is unset
        and the global one will be used"""
        return self._app
        
            
    ## -- End Interface -- @}
# end class CommandBase


class SubCommandBase(CommandBase, ISubCommand):
    """Base implementation for SubCommands to work with any compatible main command.
    
    Compatibility is determined by comparing the name of the given command with the name we see in 
    our configuration.
    
    The SubCommand's name will also serve as name used to refer to it. For example, a subcommand named 'list'
    will be accessible through 'main list ...' .
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # To be configured by subtypes
    # @{
    
    ## The name of the main command we should be compatible with
    main_command_name = None

    ## We never want to create an application, and assume it's done in the main command
    ApplicationType = None
    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Interface Implementation
    # @{
    
    def is_compatible(self, command):
        """@return True if the given command's name"""
        assert self.main_command_name
        return command.info_data().name == self.main_command_name
    
    ## -- End Interface Implementation -- @}

# end class SubCommandBase
