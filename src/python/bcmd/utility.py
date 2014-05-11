#-*-coding:utf-8-*-
"""
@package bcmd.utility
@brief Some utilities for general command use

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['CommandArgumentParser', 'ArgparserHandledCall', 'CommandlineOverridesMixin', 'InputError']

import sys

from .argparse import ArgumentParser


# ==============================================================================
## @name Exceptions
# ------------------------------------------------------------------------------
## @{

class InputError(Exception):
    """Thrown if one of the inputs to the commands turned out to be invalid"""
    __slots__ = ()
    

# end class InputError

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

    ## -- End Configuration -- @}

    def setup_argparser(self, parser):
        try:
            super(CommandlineOverridesMixin, self).setup_argparser(parser)
        except AttributeError:
            # It can be that super doesn't work here as we are not called through a direct instance method, but like
            # CommandlineOverridesMixin.foo(self)
            pass
        # end 

        help = "Override any settings value, relative to your command's settings."
        help += 'Example: -s foo=bar --set limit=1.24'
        parser.add_argument(*self.set_args, dest='overrides', nargs='+', metavar='key=value', help=help)

        return self


    # -------------------------
    ## @name Subclass Interface
    # @{
    
    def apply_overrides(self, schema, overrides):
        """Parse overrides and set them into a new context
        @param schema KeyValueStoreSchema of your command
        @param all override values as 'key=value' string
        @note to be called in execute() method"""
        if not overrides:
            return
        # end early bailout

        env = self.application().context().push('user overrides')
        kvstore = env._kvstore
        for kvstring in overrides:
            tokens = kvstring.split('=')
            if len(tokens) != 2:
                raise InputError("format of user-override is 'key=value', got '%s'" % kvstring)
            #end verify format
            key, value = tokens
            if value.startswith('['):
                try:
                    value = eval(value)
                except Exception:
                    raise InputError("Failed to parse '%s' as a list" % value)
                # end handle conversion
            # end handle 
            kvstore.set_value('%s.%s' % (schema.key(), key), value)
        # end for each string to apply

    ## -- End Subclass Interface -- @}

# end class CommandlineOverridesMixin

## -- End Types -- @}
