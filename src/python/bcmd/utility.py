#-*-coding:utf-8-*-
"""
@package bcmd.utility
@brief Some utilities for general command use

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['CommandArgumentParser', 'ArgparserHandledCall', 'CommandlineOverridesMixin', 'InputError', 
           'SuccessfulBreak']

import sys

from bapp import ApplicationSettingsMixin
from butility import parse_key_value_string
from .argparse import ArgumentParser


# ==============================================================================
## @name Exceptions
# ------------------------------------------------------------------------------
## @{

class InputError(Exception):
    """Thrown if one of the inputs to the commands turned out to be invalid"""
    __slots__ = ()
    
# end class InputError


class SuccessfulBreak(Exception):
    """An exception indicating that everything is alright.
    Useful if particular implementations want to break out of a call"""
    __slots__ = ()


# end class SuccessfulBreak

## -- End Exceptions -- @}


# ==============================================================================
## @name Types
# ------------------------------------------------------------------------------
## @{

class ArgparserHandledCall(Exception):
    """An exception to indicate the arg parser handled the logic already.
    This usually happens if the commandline was called in help mode, or when showing the version"""
    __slots__ = 'message'
    def __init__(self, message):
        self.message = message
        

class CommandArgumentParser(ArgumentParser):
    """Our version of the argument parser which will not exit on error, but raise instead"""
    __slots__ = ()

    def exit(self, status=0, message=None):
        """Raise on error, instead of exiting
        @return status in case there is no message (i.e. the parser just wanted to exit)"""
        if status == 0:
            raise ArgparserHandledCall(message) 
            
        # reraise if possible
        exc_type, value, traceback = sys.exc_info()
        if value:
            raise
        else:
            assert message, "should have gotten an argparser message"
            raise Exception(message)
        # END options
    

# end class CommandArgumentParser


class CommandlineOverridesMixin(object):
    """Subtypes will allow very straight-forward overrides to their context values, which looks nicer 
    than using the wrapper.

    For example:

        cmd ---yourcommand.myvalue=1 ---yourcommand.othervalue=2 [...]

    becomes

        cmd --set myvalue=1 othervalue=2 [...]

    However, the wrapper's capabilities are used to set the context

        cmd @project/A --your-arg --set myvalue=1 [...]

    Usage
    =====

    Derive from the type, and call 'self.apply_overrides()' during execute(). You must define a schema informing
    about the values you can support, and where to find them.
    """
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{

    ## the arguments we take on the commandline    
    set_args = ['--set']

    ## If set, and if we have a schema, our configuration
    show_config_args = ['-c', '--show-settings']

    ## separator between keys and values
    key_value_separator = '='

    ## -- End Configuration -- @}

    def setup_overrides_argparser(self, parser):
        help = "Override any settings value, relative to your command's settings."
        help += 'Example: -s foo=bar --set limit=1.24'
        parser.add_argument(*self.set_args, dest='overrides', nargs='+', metavar='key=value', help=help)

        if self.show_config_args:
            help = "Show the daemons effective configuration and exit"
            parser.add_argument(*self.show_config_args, default=False, 
                                    dest='show_settings', action='store_true', help=help)
        # end handle commandargs

        return self


    # -------------------------
    ## @name Subclass Interface
    # @{
    
    def apply_overrides(self, schema, args):
        """Parse overrides and set them into a new context
        @param schema KeyValueStoreSchema of your command
        @param all override values as 'key=value' string
        @note to be called in execute() method"""
        if args.overrides:
            env = self.application().context().push('user overrides')
            kvstore = env._kvstore
            for kvstring in args.overrides:
                k, v = parse_key_value_string(kvstring, self.key_value_separator)
                kvstore.set_value('%s.%s' % (schema.key(), k), v)
            # end for each string to apply
        # end handle overrides

        if getattr(args, 'show_settings', None):
            sys.stdout.write("%s.*\n" % schema.key())
            sys.stdout.write(str(self.application().context().settings().value_by_schema(schema)))
            raise SuccessfulBreak
        # end handle settings
    ## -- End Subclass Interface -- @}

# end class CommandlineOverridesMixin

## -- End Types -- @}
