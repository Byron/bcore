#-*-coding:utf-8-*-
"""
@package bcore.template.exceptions
@brief Contains all exceptions used by the bcore.template package

@copyright 2012 Sebastian Thiel
"""
__all__ = ['Error', 'InvalidValueError', 'MissingFormatResultError']

import bcore

class Error(bcore.Error):
    """Base exception for all exceptions thrown by bcore.template"""
    __slots__ = ()

class InvalidValueError(Error):
    """Thrown when the VerifiedElementNode cannot assure the validity of a value.
    
    It contains the fully qualified key of the data entry, as well as an explanation about the issue"""
    __slots__ = (
                    'key',          ## fully qualified key that caused the isse
                    'annotation'   ## more information about the issue
                )
    
    def __init__(self, key, annotation):
        super(InvalidValueError, self).__init__()
        self.key = key
        self.annotation = annotation
        
        
class MissingFormatResultError(Error):
    """Thrown if a StringFormatNode that didn't have a substitution result was used to generate a string"""
    __slots__ = (
                    'node'          ## The node which caused the issue
                )

    def __init__(self, node):
        """Initialize this instance"""
        super(MissingFormatResultError, self).__init__()
        self.node = node
    

# end class MissingFormatResultError
    

# end class Error
