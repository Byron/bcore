#-*-coding:utf-8-*-
"""
@package standard_module
@brief Brief information about this module, mandatory !

Markdown Support
================

Within doc-strings, you may use the complete set of doxygen markup. Each markup
item is preprended with an @ character, instead of backslash. This allows us
to use standard docstrings, instead of the raw versions (r''), which would proabbly
be forgotten anyway.

Using [Markdown](http://www.stack.nl/~dimitri/doxygen/markdown.html), you can write a whole lot of good-looking documentation right into
your doc-string.

Level 2 Header
--------------
This is an example of some standard mark-down, which has some similarity
standard restructured text, making it easy to read even in-source.

> Here is a quote
> spanning multiple lines

Its easy to create unordered lists too:

- Item 1

  More text for item 1
  
- Item 2
  + Nested Item 1
  + Nested Item 2
- Item 3

Ordered lists are created as follows:

1. Ordered List Item 1
2. Ordered List Item 2
   + Nested Item 1
   + Nested Item 2
   
Verbatim block can be made by indenting it by at least 4 spaces:

    This text will
    show up 
    verbatim
    

Text Formatting
===============

*italic*, _italic too_.

And this will be **bold**, and __bold as well__.

Put `code()` into backticks to render it in a `monospaced` font. Literal backticks
are created by ``escaping`` them with backticks.

Links
-----
[Link to google](http://google.com)

Additional Reading
==================
[Read more about the Markdown syntax ...](http://www.stack.nl/~dimitri/doxygen/markdown.html)



@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
#! A module-level __all__ is required to make from module import * save, which 
#! may be by parent-packages exclusively. For anything else, we need to be 
#! explicit.
__all__ = [ 'Conjugator', 'ControlConjugator', 'HighlevelControlConjugator',
            'function', 'function_without_group' ]

#! Generally order your imports (naturally) by dependency. Therefore, the most
#! independent modules and packages are imported first.
#! Usually these are the built-in packages, which makes them come first, always.
#! See http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=Imports_formatting#Imports_formatting

#! first import block gets standard python libraries 
import os
import sys

#! from x import * statements have their own section within the import block
from re import match


#! second import block gets our own libraries, which follow optional 
#! third-party libraries
import bapp
import bapp.log

#! from x import * statements have a separate block
from bapp import one
from bapp.package import (
                            first,
                            second
                        )


# ==============================================================================
## @name Constants
# ------------------------------------------------------------------------------
# Optional Description here
# and there multiline
## @{

## A magic number on module level
MAGIC_NUMBER = 5

## -- End Constants -- @}


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
# Optional Description
## @{

def function(arg1, kwarg='value'):
    """Perform a function
    
    @param arg1 is first arg
    @param kwarg is first key-value arg
    
    @note has sideeffects
    """
    pass

## -- End Utilities -- @}


def function_without_group(hello):
    """A function outside of a group.
    
    @param hello info about hello"""
    pass


#! This section is in fact ignored by doxygen, we may use it anyway 
#! to group entities 
# ==============================================================================
## @name Section for Classes
# ------------------------------------------------------------------------------
## @{

class Conjugator(object):
    """A base class for all types in this module"""
    #! Make sure all your bases have slots, otherwise derived types
    #! will get a dict anyway even if they define slots themselves.
    __slots__ = tuple()
    
    ## @name Interface
    # -------------------------
    # @{
    
    def conjugate(self, verb, casus):
        """Conjugates a given verb to the given casus
        
        @param verb a verb
        @param casus a case to which to conjugate the verb
        @return the conjugated verb as string
        """
        raise NotImplementedError("TBD by Sub-Type")
    
    ## -- Interface -- @}
    
# end class Conjugator


class ControlConjugator(Conjugator):
    """a brief description
    
    Now comes the long description with information on what it does and how to
    use it.
    
    Example usage:
    @code
    instance = One(1)
    instance.method()
    
    if(instance):
        pass
    else:
        pass
    @endcode
    """
    __slots__ = (
                '_member',       # holds important information
                '_other_member'  # docs for doxygen
                )
    
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Describe how this type is used
    # A basic implementation for a network controller we use (and instantiate
    # internally)
    _network_controller_type = Something
    
    ## An option that can take values between 1 and (excluding) 6
    _some_option = 5
    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Constants
    # Optional Description - please note that the variables are just constant
    # by definition.
    # @{
    
    ## a constant magic number
    magic_number = 1
    
    ## -- End Constants -- @}
    
    def __init__(self, arg1, kwarg='default'):
        """Initialize this instance
        
        @param arg1 does this
        @param kwarg does something else, defaults to "default"
        """
        self._member = arg1
        self._other_member = kwarg
        
    def __del__(self):
        """Cleanup this instance"""
        pass
    
    # -------------------------
    ## @name Interface
    # @{
    
    def conjugate(self, verb, casus):
        #! Will inherit docs of the base implementation
        return verb + casus
    
    ## -- Interface -- @}
    
    # -------------------------
    ## @name Protected Methods
    # Optional Description
    # @{
    
    def _some_internal_function(self):
        """Perform an internal operation"""
        pass
    
    # -- End Protected Methods -- @}
    
    # -------------------------
    ## @name Protocol
    # Optional Description
    # @{
    
    def __call__(self):
        """Make this type a callable"""
        pass
    
    ## -- End Protocol -- @} 
    
    # -------------------------
    ## @name Read-Only Methods
    # Optional Description
    # @{
    
    @decorator(arg)
    def method(self, *args, **kwargs):
        """Method docs
        
        @param *args a variable arg list
        @param **kwargs a dict of key-value args
        @return some product as string
        """
        for i in range(10):
            if i % 2:
                i = i * 2
            #end if i % 2
        #end for i in range
        return i * self.member()
        
    ## -- End Read-Only Methods -- @} 
    
    # -------------------------
    ## @name Accessors
    # Optional Description
    # @{
    
    def member(self):
        #! Has no docstring as its obvious what the method does 
        return self._member
        
    def set_member(self, new_member):
        """Set ourselves a new member, which may not be None
        
        \throw ValueError if new_member is None
        """
        if new_member is None:
            raise ValueError("new_member may not be None")
        self._member = new_member
        
    ## -- End Accessors -- @} 

# end class ControlConjugator


class HighlevelControlConjugator(ControlConjugator):
    """Brief information about class Two
    
    Some more details on usage etc.
    """
    
    __slots__ = '_yet_another_member'       # just a single member, and say what it does
    
    ## A private class member
    _first_instance = None
    
    
    # -------------------------
    ## @name Interface
    # @{
    
    def conjugate(self, verb, casus):
        #! Will inherit docs of the base implementation
        return "highlevel %s %s !" % (verb, casus)
    
    ## -- End Interface -- @}
    
    def method(self, *args, **kwargs):
        """Overrides base class with some special functionality
        
        Its not in a group, which is fine as well.
        """
        super(HighlevelControlConjugator, self).method(*args, **kwargs)

# end class Two

##  -- End Classes -- @}


