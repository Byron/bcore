# -*- coding: utf-8 -*-
"""
@package bcore.core.component.exceptions
@brief exceptions raised by the component architecture

@copyright 2012 Sebastian Thiel
"""

__all__ = ['InheritanceException', 'ServiceNotFound', 'EnvironmentNotFound', 'PushEnvDenied']

import bcore

## @name EXCEPTIONS
#  ----------------
## @{

class InheritanceException(bcore.Error):
    """ Raised when there's an illegal inheritance detected in interfaces
        and plugins """
    def __init__(self, cls, new_base, conflict_base):
        """ cls is supposed to inherit from new_base, which is a subclass
            of conflict_base, which creates a non deterministic MRO
        """
        self._cls = cls
        self._new_base = new_base
        self._conflict_base = conflict_base

    def __str__(self):
        return "%s can't inherit from %s, it already inherits from %s which is a superclass of %s" % (self._cls, self._new_base, self._conflict_base, self._new_base)

class ServiceNotFound(bcore.Error):
    """ Raised when a service is searched for, but none are found """
    def __init__(self, interface):
        self._interface = interface

    def __str__(self):
        return "No service found for interface %s" % (self._interface)

class EnvironmentNotFound(bcore.Error):
    """ Raised when an environment is searched for on the stack and is not found """
    def __init__(self, search_parameter, match_type):
        self._search_parameter = search_parameter
        self._match_type       = match_type

    def __str__(self):
        return "Environment with %s == %s not found on the stack" % (self._match_type, self._search_parameter)

class PushEnvDenied(bcore.Error):
    """ Raised when an environment can't be pushed onto the stack """
    def __init__(self, environment_name, reason):
        self._reason = reason
        self._environment_name = environment_name

    def __str__(self):
        return "Can't push %s onto the stack: %s" % (self._environment_name, self._reason)

# -- End EXCEPTIONS --
## @}
