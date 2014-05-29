#-*-coding:utf-8-*-
"""
@package bapp.tests.base
@brief most fundamental types

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""

import logging

import bapp
from butility.tests import TestCase
from butility import (Path,
                      wraps,
                      partial)

from bapp import (preserve_application)

log = logging.getLogger('bapp.tests')


# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

def with_application(fun=None, **dkwargs):
    """similar to preserve_application(), but will create a new application object that will 
    be discarded once the decorated function completes.
    It's useful if there is ApplictionSettingsClient code that tries to access the central information database
    @param dkwargs are given to bapp.Application.new()
    @note you can use the custom parameter from_file=__file__ to append the given file to the settings_trees of
    the new application.
    @note you may also specifiy the application type using the application_type kwargument. It should not definitely
    not load the ProcessEnvironment, in case this process is already wrapped.
    It will also make sure the stack receives the initial types, which were gathered by the default context
    while there was no application"""
    if fun is None:
        p = partial(with_application, **dkwargs)
        p.__module__ = p.__name__ = str()
        return p
    # end handle custom arguments

    @wraps(fun)
    def wrapper(*args, **kwargs):
        from_file = dkwargs.pop('from_file', None)
        application_type = dkwargs.pop('application_type', bapp.Application)
        prev = bapp.Application.main
        if from_file:
            settings_trees = dkwargs.setdefault('settings_trees', list())
            settings_trees.append(Path(from_file).dirname())
        # end handle arguments
        # never load user settings
        dkwargs['user_settings'] = False
        app = application_type.new(**dkwargs)

        # Make sure the default context is inserted, if it doesn't have it
        default_ctx = None
        for ctx in app.context().stack():
            if ctx.name() == bapp.Application.PRE_APPLICATION_CONTEXT_NAME:
                default_ctx = ctx
                break
            # end context found
        # end find default context if possible

        if default_ctx is None and bapp.Application.Plugin.default_stack:
            # We have incredible knowledge about this implementation, and probably shouldn't use it !
            # We know there is a default 
            assert len(bapp.Application.Plugin.default_stack) == 1
            default_ctx = bapp.Application.Plugin.default_stack.stack()[0]
            app.context().insert(0, default_ctx)
        # end 

        try:
            return fun(*args, **kwargs)
        finally:
            # put the transferred and possibly existing default context back
            if default_ctx:
                # yes, it may be that it wasn't needed when we arrived here
                assert len(bapp.Application.Plugin.default_stack) == 0
                bapp.Application.Plugin.default_stack.push(default_ctx)
            # end restore default context

            # we don't have to do anything with the default context, it will just remain in the origin
            bapp.Application.main = prev
        # end assure original application is put back
    # end wrapper
    return wrapper
    

## -- End Decorators -- @}


# ==============================================================================
## @name Types
# ------------------------------------------------------------------------------
## @{

class AppTestCase(TestCase):
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

# end class TestCase

## -- End Types -- @}





