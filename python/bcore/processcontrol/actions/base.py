#-*-coding:utf-8-*-
"""
@package bcore.processcontrol.actions.base
@brief Base implementation of action handler

@copyright 2013 Sebastian Thiel
"""
__all__ = ['ActionDelegateMixin', 'PackageActionBase']

import bcore
from bcore.processing.transaction import (
                                        Transaction,
                                        Operation
                                      )

from .schema import action_schema

class PackageActionBase(Operation):
    """An action to perform right before the process is started.

    @note yet another implementation of the command pattern
    """
    __slots__ = (
                    'package_name',
                    'package_data',
                    'action_data',
                    'action_name',
                )

    # -------------------------
    ## @name Configuration
    # @{

    ## Should be the schema matching the particular action type.
    ## It can be used to obtain a value from a kvstore, where key is a computed value based on our name
    ## @note To be set by subclass
    action_schema = None

    ## A name for the type of action. It is used as key when accessing a kvstore
    type_name = None

    ## -- End Configuration -- @}


    # -------------------------
    ## @name Delegate Configuration
    # Properties read by the ProcessControllerDelegate to alter its behaviour
    # Any property can be used, effectively it depends on the delegate to try to read them depending
    # on what kind of PackageAction it sees
    # @{

    ## If True or False, the delegate should use this return value when asked for whether or not to spawn
    ## Has no effect if it is None
    delegate_must_spawn = None
    
    ## -- End Delegate Configuration -- @}

    def __init__(self, transaction, name, data, package_name, package_data):
        """Every instance of an action has information about the package that it was instantiated for,
        but will additionally query information about the action's data itself
        @param transaction 
        @param name name of the action
        @param data data block for the action, as retrieved by the data() classmethod
        @param package_name name of the package that referred to the action
        @param package_data data block as received by KeyValueStoreProvider.value() function
        """
        self.action_name = name
        self.action_data = data
        self.package_name = package_name
        self.package_data = package_data
        super(PackageActionBase, self).__init__(transaction)

    # -------------------------
    ## @name Interface
    # @{

    @property
    def name(self):
        """@return the name of our action, for compatibility to our base type"""
        return self.action_name

    @classmethod
    def data_key(cls, name):
        """@return this package's data based on the given  name, normalized to fit our schema
        @param cls
        @param name name of the action"""
        assert cls.type_name is not None, "'type_name' to be set in subclass"
        return action_schema.key() + '.' + cls.type_name + '.' + name
        
    @classmethod
    def data(cls, key, kvstore = None):
        """@return the datablock suitable for instantiating an action with, based on the action's schema
        @throw ValueError if the given data key does not exist
        @param cls
        @param key key at which the kvstore should be sampled, usually created by data_key()
        @param kvstore store to use. Default store will be used if None"""
        kvstore = kvstore or bcore.environment.context()
        assert cls.action_schema is not None, "'action_schema' to be set in subclass"
        if not kvstore.has_value(key):
            raise ValueError("Action at key '%s' doesn't exist" % key)
        return kvstore.value(key, cls.action_schema, resolve=True)
        
    ## -- End Interface -- @}

# end class PackageAction


class ActionDelegateMixin(object):
    """Adds support for a transaction to store operations in.

    @note it's meant to be a one-shot item
    """
    __slots__ = (
                    '_transaction'
                )

    # -------------------------
    ## @name Configuration
    # @{

    name = "ProcessControllerTransaction"
    TransactionType = Transaction
    
    ## -- End Configuration -- @}

    def __init__(self):
        self._transaction = None

    # -------------------------
    ## @name Interface
    # @{

    def transaction(self):
        """@return a transaction instance
        @!note it will always be the same one after the first call"""
        if self._transaction is None:
            self._transaction = self.TransactionType(service(bcore.ILog).new(self.name))
        # end initialize transaction
        return self._transaction

    def has_transaction(self):
        """@return True if we have created a transaction already during a call to transaction()"""
        return self._transaction is not None

    def action(self, key):
        """@return an action implementation matching the given name key
        @note this implementation looks for registered services
        @throw AssertionError if no suitable action was found"""
        tokens = key.split('.')
        assert len(tokens) > 2, "expected action key of format %s.type_name.name[.name...]" % action_schema.key()
        type_name = tokens[1]
        for cls in bcore.environment.classes(PackageActionBase):
            if cls.type_name == type_name:
                return cls
        # end for each class
        raise AssertionError("Couldn't find action of type '%s'" % type_name)
    ## -- End Interface -- @}
# end class PackageTransaction

