#-*-coding:utf-8-*-
"""
@package bcore.component.base
@brief A from scratch implementation of a component architecture, influenced by
experiences with the pyutilib CA

services
-------------
standard predicates used in EnvironmentStack.services

default is ServiceAll and CreateNever, meaning return all services
found and don't create anything. factory mode would be using ServiceNone
 and Createalways
 
### create predicates ###

must return a boolean controlling whether a cls found matching an
interface should be instantiated and included in the return set
they have these parameters:
  
* icls        : the class that is being considered for instantiation
* interface   : the interface that is being searched for
* services    : services found so far
* classes      : classes found so far
  
### service predicate ###
decide whether an existing service that was found matching an interface
should be considered a match and thus be included in the return set
they have these parameters:
  
* service     : the service considered for inclusion in the return value
* interface   : the interface that is being searched for

@copyright 2012 Sebastian Thiel
"""
__all__ = ['Plugin', 'PluginMeta',
           'Environment', 'EnvironmentStack', 'PluginLoader',
           'CreatePredicate', 'ServicePredicate',
           'CreateAlways', 'CreateMissing', 'CreateFirst',
           'ServiceAll', 'ServiceNone', 'EnvironmentStackContextClient',
           'StackAutoResolveAdditiveMergeDelegate',
            'service', 'new_service', 'services', 'new_services']


## These items will go into the builtin namespace, and thus be available everywhere
__for_builtin__ = [ 'Plugin', 'EnvironmentStackContextClient', 'PluginLoader', 'service', 'services', 
                    'new_service', 'new_services', 'ServiceNotFound']

import os
import sys
import re
import imp
import inspect
import itertools

import bcore
from bcore.log import module_logger
from bcore.utility import (
                        OrderedDict,
                        LazyMixin
                       )

from bdiff import (
                            NoValue,
                            TwoWayDiff,
                            AutoResolveAdditiveMergeDelegate
                         )
from bkvstore import (
                                KeyValueStoreSchemaValidator,
                                KeyValueStoreModifier,
                                KeyValueStoreSchema,
                                RootKey
                            )
from bcore.component.exceptions import *
from bcore.path import Path

log = module_logger(__name__)


# ==============================================================================
## @name Predicates
# ------------------------------------------------------------------------------
## @{

# disable no __init__ warning (which would never be called anyway)
# disable eval's arguments being different in different cases
# pylint: disable=W0232,W0221

# yes, we are using * magic here
# pylint: disable=W0142
class Predicate(object):
    """ a class that returns the result of its eval() method on creation,
        with dynamic argument list passed to eval based on that method's
        signature
    """
    # signature of *opts passed to the constructor
    # eval can accept between none or all of these arguments
    _args = []
    
    def __new__(cls, *opts):
        """@return the result of calling eval with the arguments specified in 
            eval()'s signature """
        # make a dictionary of the *opts, so we can access the values by name
        map_args = dict(zip(cls._args, opts))
        keys = inspect.getargspec(cls.eval)[0]
        eval_opts = [map_args[k] for k in keys if k in cls._args]
        return cls.eval(*eval_opts)

    @staticmethod
    def eval():
        """ can have any subset of the standard arguments of the parent class 
        """
        pass
# end class Predicate
# pylint: enable=W0142

class CreatePredicate(Predicate):
    """ creation predicate used in bcore.environment.services """
    _args = ['icls', 'services', 'classes']
    def __init__(self, icls, services, classes):
        raise NotImplementedError


class ServicePredicate(Predicate):
    """ services predicate used in bcore.environment.services """    
    _args = ['service', 'interface']
    
    def __init__(self, service, interface):
        raise NotImplementedError


class CreateAlways(CreatePredicate):
    """ always create everything """
    @staticmethod
    def eval():
        return True


class CreateMissing(CreatePredicate):
    """ instantiate all missing services that haven't been created yet """
    @staticmethod
    def eval(icls, services):
        """ check if any of the services available so far already implement icls """
        return not bool(filter(lambda service: str(type(service)) == str(icls),  services))


class CreateFirst(CreatePredicate):
    """ only instantiate one service if it hasn't been found yet """
    @staticmethod
    def eval(services):
        return len(services) == 0


class ServiceAll(ServicePredicate):
    """@return all services already instantiated """
    @staticmethod
    def eval():
        return True


class ServiceNone(ServicePredicate):
    """ do not return any services already instatiated"""
    @staticmethod
    def eval():
        return False

# pylint: enable=W0232,W0221

## -- End Predicates -- @}

# ==============================================================================
## @name Convenience Utilities
# ------------------------------------------------------------------------------
## Functions provided here use the globals to perform a very specific action. They should
## help to make the component system very usable
## @{

def service(interface, predicate = ServiceAll):
    """@return the first found provider implementing the given interface. The service is persistent and owned 
    by the environment
    @param interface a class/type, that the service you seek needs to implement
    @param predicate function(service, interface) returning True for each service instance of type 
    interface that may be returned 
    @throw ServiceNotFound if there is no such service
    @note use this function assuming that you will receive a service, no checking necessary. The code setting 
    up the environment will assure there is at least one implementation. Otherwise its a bug somewhere else."""
    svcs = services(interface, predicate = predicate)
    if not svcs:
        raise ServiceNotFound(interface)
    # end handle no service
    return svcs[0]
    
def services(interface, predicate = ServiceAll):
    """@return a list of services which provide the given interface, or an empty list if there was 
    no such service. The services will always be persistent ones.
    @param interface a class/type that the services you seek need to implement
    @param predicate function(service, interface) returning True for each service instance of type interface 
    that may be returned"""
    return bcore.environment.services(interface, predicate = predicate)
    
def new_service(interface, *args, **kwargs):
    """@return a newly created instance of a service supporting the given interface.
    It is temporary as such the caller receives ownership. Therefore it will not be returned when it
    someone queries a simpilar interface
    @param interface service to be found needs to implement the given interface
    @param args arguments to be passed to service constructor
    @param kwargs keyword arguments to be passed to service constructor
    @throw ServiceNotFound if there is no such service"""
    svcs = bcore.environment.new_services(interface, take_ownership = False, predicate = CreateFirst, args = args, kwargs = kwargs)
    if not svcs:
        raise ServiceNotFound(interface)
    # handle no service found
    # Newest services will be returned first
    return svcs[0]
    
def new_services(interface, *args, **kwargs):
    """@return a list of newly created services which implement the given interface, or an empty list.
    Service instances will be created for *all* service types that support the given interface. 
    @note the created service instance will be owned only by you, and will therefore never be returned when asking 
    for \ref services .
    @param interface that services must implement
    @param args arguments to be passed to service constructor
    @param kwargs keyword arguments to be passed to service constructor 
    """
    return bcore.environment.new_services(interface, take_ownership = False, predicate = CreateAlways, args = args, kwargs = kwargs)
    
## -- End Convenience Utilities -- @}



# ==============================================================================
## @name Flags
# ------------------------------------------------------------------------------
## @{

## identifier for the base environment on the stack and
## the category name for environments that do not set their own
BASE_IDENTIFIER = "$base$"

## -- End Flags -- @}


# ==============================================================================
## @name Environments
# ------------------------------------------------------------------------------
## @{

class EnvironmentStackContextClient(bcore.InterfaceBase):
    """Base implementation to allow anyone to safely use the context of the global environment stack.
    Everyone using the global context should derive from it to facilitate context usage and to allow the 
    EnvironmentStack to verify its data.
    
    This type basically brings together a schema with another type, to make data access to any context easy
    """
    __slots__ = ()

    ## Schema specifying how we would like to access the global environment context 
    ## It must be set by subclasses if they access the context
    ## The base implementation of schema() will just return this class-level instance, per instance 
    ## schemas are generally possible though
    _schema = None 
    
    @classmethod
    def schema(cls):
        """@return our schema instance, by default it will return the class level instance
        """
        assert isinstance(cls._schema, KeyValueStoreSchema), "Subclass must provide a schema instance"
        return cls._schema
        
    @classmethod
    def context_value(cls, context=None, resolve=True):
        """@return a nested dict with getattr access as obtained from the current EnvironmentStack's context, 
        validated against our schema.
        @param cls
        @param context if not None, use the given context (KeyValueStoreProvider) instead of the global one
        @param resolve if True, string values will be resolved
        @note use this method when you need access to the datastructure matching your schema"""
        schema = cls.schema()
        return (context or bcore.environment.context()).value(schema.key(), schema, resolve=resolve)
        
# end class EnvironmentStackContextClient



class StackAutoResolveAdditiveMergeDelegate(AutoResolveAdditiveMergeDelegate):
    """A delegate which implements special rules for handling of values which are not supposed 
    to be overridden. Additional behaviour could be implemented as needed"""
    __slots__ = ()

    def _resolve_conflict(self, key, left_value, right_value):
        """Check for forced overrides and provide the correct value"""
        res = super(StackAutoResolveAdditiveMergeDelegate, self)._resolve_conflict(key, left_value, right_value)
        if res is right_value and hasattr(left_value, 'endswith') and left_value.endswith('!'):
            return left_value[:-1]
        # end handle override
        return res
    
# end class StackAutoResolveAdditiveMergeDelegate 


class Environment(EnvironmentStackContextClient):
    """ Maintains a dictionary of interface => services and interface => classes
        allows searching for services and classes by interface
        keeps a context in a kvstore which acts like a simple hierarchical database
        @note This class is extended into a composite environment which is what
              is actually on the env stack
    """
    __slots__ = (
                    '_name',     # name of the environment
                    '_registry', # a list of instances and types 
                    '_kvstore'   # the environments context as kvstore
                )
    
    # -------------------------
    ## @name Configuration
    # documentation
    # @{
    
    ## it's possible to find environments by category, which is matched against _category
    _category = BASE_IDENTIFIER
    
    ## Type used to instantiate a kv store modifier
    KeyValueStoreModifierType = KeyValueStoreModifier
    
    ## To make usage easier, we assume we don't actually use the context
    _schema = KeyValueStoreSchema(RootKey, dict())
    
    ## -- End Configuration -- @}
    
    def __init__(self, name):
        """ @param name searchable name of this environment"""
        self._name  = name
        self.reset()
        
    def __repr__(self):
        return "Environment %s" % (self._name)
        
    def _contents_str(self):
        """Display the contents of the environment primarily for debugging purposes
        @return string indicating the human-readable contents"""
        otp = str(self)
        otp += "\t* registered services|types:\n"
        for item in self._registry:
            otp += "\t%s\n" % item
            # Could list supported interfaces here
        otp += "\t* context:\n"
        otp += re.sub(r"(^|\n)", r"\1\t", str(self._kvstore)) + '\n'
        return otp
        
    # -------------------------
    ## @name Attributes
    # Simple attributes to categorize the environment
    # @{
    
    def name(self):
        """@return our name"""
        return self._name

    def category(self):
        """@return our category"""
        return self._category
        
    ## -- End Attributes -- @}
    
    # -------------------------
    ## @name Query Interface
    # @{
    
    def _filter_registry(self, interface, predicate):
        """Iterate the registry and return a list of matching items, but only consider registrees for which 
        predicate returns True"""
        items = list()
        # Items that came later will be used first - this way items that came later can override newer ones
        for item in reversed(self._registry):
            if predicate(item) and (interface is None or 
                        (isinstance(item, interface) or (isinstance(item, type) and issubclass(item, interface)))):
                items.append(item)
            # end if registree is suitable
        # end for each registered item
        return items
    
    def _classes(self, interface = None):
        """@return all classes registered as implementing \a interface
            @param interface   : the interface to search for,
                                 or return all if it's None
        """
        return self._filter_registry(interface, lambda x: isinstance(x, type))
    
    def services(self, interface=None):
        """@return all services registered as implementing \a interface
            @param interface : the interface to search for,
                               or return all if it's None
        """
        return self._filter_registry(interface, lambda x: not isinstance(x, type))
        
    ## -- End Query Interface -- @}

    # -------------------------
    ## @name Edit Interface
    # @{
            
    def _context(self):
        """@returns a our context
        @note changes to it will be reflected in the environment"""
        return self._kvstore
        
    def _register(self, plugin):
        """ register an instantiated plugin as implementing \a interface
            @param plugin : the plugin instance to register or the class to use for instantiation
            @note we are save and will not add duplicates to the registry 
            @return self
        """
        if plugin not in self._registry:
            self._registry.append(plugin)
        return self
        
    def _set_context_value(self, value):
        """Set the given possibly nested value to our own kvstore, using our schema to know where to put it
        @return self"""
        self._kvstore.set_value(self.schema().key(), value)
        return self
        
    
    def reset(self):
        """ we forget all our classes and services, as well as our context"""
        self._kvstore = self.KeyValueStoreModifierType(OrderedDict())
        ## registry of instantiated plugins claiming to implement certain interfaces
        ## values: tuple(plugin, implemented_interface)
        self._registry = list()
        
    ## -- End Edit Interface -- @}

# end class Environment


class EnvironmentStack(LazyMixin):
    """ maintains a stack of envrionments.
        returns services by searching through this stack
        registers services in the current environment.
        Will always have (and keep) a base environment that serves as 'catch all' environment.
        Once instantiated, a plugin cannot be deleted (it is owned by the environment) until the environment
        itself is removed
    """
    __metaclass__ = bcore.MetaBase
    __slots__ = (   
                    '_stack', 
                    '_kvstore',
                    '_base_environment_type',
                    '_num_aggregated_environments'         # number environments aggregated in our current cache
                )
    
    # stack recursion
    ## stay on the current stack level
    ## recurse until the bottom of the stack
    RECURSE_ALWAYS      = 'recurse_always'
    ## recurse the stack until we found what was being searched for
    RECURSE_UNTIL_FOUND = 'recurse_until_found'
    
    # -------------------------
    ## @name Configuration
    # @{
    
    _EnvironmentType = Environment
    
    _KeyValueStoreValidatorType = KeyValueStoreSchemaValidator
    
    ## -- End Configuration -- @}

    def __init__(self, base_environment_cls = None):
        self._stack = list() # the stack itself
        self._base_environment_type = base_environment_cls or self._EnvironmentType
        self.reset(new_base = True)
        
    def _set_cache_(self, name):
        if name == '_kvstore':
            self._kvstore = self._aggregated_context()
        else:
            return super(EnvironmentStack, self)._set_cache_(name)

    def __str__(self):
        return ''.join(self._walk_stack(self.RECURSE_ALWAYS, lambda env: str(env)+"\n"))
    
    def _contents_str(self):
        """ print a comprehensive representation of the stack 
            @todo convert this into returning a data structure which would be useful and printable            
        """
        otp = str()
        for idx, env in enumerate(self._stack):
            otp += "### Environment %i - %s ###############\n\n" % (idx, env.name())
            otp += env._contents_str()
        # for each env on stack
        return otp
        
    def _mark_rebuild_changed_context(self):
        """Keep our changes and re-apply them to a rebuilt copy
        @todo implement the change-re-application similar to what the YAMLstore does"""
        # triggers a rebuild on next access
        try:
            del(self._kvstore)
        except AttributeError:
            pass
        # ignore missing context
        self._num_aggregated_environments = 0
        
    def register(self, plugin):
        """registers plugin as a service providing all interfaces it derives from
            @param plugin any instance or class  
        """
        self.top()._register(plugin)
        
    # -------------------------
    ## @name Protocols
    # @{
    
    def __len__(self):
        """@return the length of the environment stack """
        return len(self._stack)
    
    ## -- End Protocols -- @}
    
    # -------------------------
    # Internal Query Interface
    #
    
    def _env_stack_readonly(self):
        """@return our environment stack, reference. Must be treated read-only, as well as the environments
        @note can be used by environments to search the stack directly. Its a very private interface, and 
        just for very specific purposes, """
        return self._stack
    
    def _walk_stack(self, recurse, fresult, *opts, **kwargs):
        """ recurse through the stack, calling f on the environment at index \a idx
            with opts and kwargs
            @param recurse : RECURSE_FOO flags control our recursion through the stack
            @param fresult : function to call for the environment we're on,
                       needs to return results that can be added with '+'
            @param opts/kwargs : passed to f
        """
        result = list()
        for env in reversed(self._stack):
            result += fresult(env, *opts, **kwargs)
            if len(result) and recurse == self.RECURSE_UNTIL_FOUND:
                break
        # for each env on stack, reversed
        return result
        
    def _find_env(self, predicate):
        """ @return find first (top - down) environment matching the given predicate, or None"""
        for env in  reversed(self._stack):
            if predicate(env):
                return env
        # end for each env top down
        return None
        
    def _aggregated_context(self, aggregated_base=None, start_at = 0):
        """@return new context as aggregate of all environments on our stack, bottom up"""
        # This delegate makes sure we don't let None values override non-null values
        delegate = StackAutoResolveAdditiveMergeDelegate()
        alg = TwoWayDiff()
        
        for eid in range(start_at, len(self._stack)):
            env = self._stack[eid]
            base = delegate.result()
            if base is NoValue:
                base = aggregated_base or OrderedDict()
            # end setup base
            alg.diff(delegate, base, env._context()._data())
        # end for each environment
        self._num_aggregated_environments = len(self._stack)

        res = delegate.result()
        if res is NoValue:
            assert aggregated_base is not None
            assert isinstance(aggregated_base, OrderedDict)
            res = aggregated_base
        # end handle special case with empty dicts
        return self._base_environment_type.KeyValueStoreModifierType(res)
        
    # -- End Internal Query Interface --
    
    # -------------------------
    ## @name Query Interface
    # @{
    
    def context(self):
        """@return aggreated context of the whole environment stack,
            updates our internal context while building it,
            so the environment we're querying for context already has
            access to the updated context of the environments
         """
        kvstore = self._kvstore

        # Check if we still have to add some environments, as someone pushed in the meanwhile
        if self._num_aggregated_environments != len(self._stack):
            kvstore = self._kvstore = self._aggregated_context(kvstore._data(), self._num_aggregated_environments)
        # end update kvstore

        return kvstore
    
    def context_value(self, schema):
        """@return the possibly nested value as matching the given schema
        @note changes done to the value will not be visible by anyone but you"""
        return self.context().value(schema.key(), schema)
    
    def top(self):
        """@return the environment on the top of stack """
        return self._stack[-1]
    
    def schema_validator(self):
        """@return a KeyValueStoreSchemaValidator instance initialized with all our Environment's schemas 
        as well as registered EnvironmentStackContextClient services to allow schema and context validation"""
        validator = self._KeyValueStoreValidatorType()
        # bottom up - later environments override earlier ones
        for env in self._stack:
            validator.append(env.schema())
            # Environment returns services newest first, which is something we hereby undo to allow
            # proper schema merging.
            for client in reversed(env.services(EnvironmentStackContextClient)):
                schema = client.schema()
                if schema not in validator:
                    validator.append(schema)
                # end append schema exclusively
            # end for each client instance
        # end for each envrionments
        return validator
        
    def stack(self):
        """@return our environment stack
        @note not for general use, as you should not try to find individual environment instances. It can 
        be useful for closely bonded functions that whish to temporarily alter the stack though"""
        return self._stack
        
    ## -- End Query Interface -- @}
    
    # -------------------------
    ## @name Edit Interface
    # @{
    
    def push(self, environment):
        """ push an environment on to the stack
            @param environment : string -> push newly created empty environment
                                 or an instance of a Environment
        @return pushed environment instance (which could be a new instance now thanks to auto-conversion)
        """
        if isinstance(environment, basestring):
            environment_name = environment
            environment = None
        elif isinstance(environment, self._base_environment_type):
            environment_name = environment.name()
        else:
            raise TypeError("invalid type passed as environment")
        # end handle type for push
        if environment is None:
            environment = self._base_environment_type(environment_name)

        self._stack.append(environment)
        return environment

    def pop(self, until_size = -1):
        """
        @return top of stack environment after popping it of does not allow the base Environment to be 
        removed returns the environment removed.
        If until_size is larger -1, return value will be a correctly sorted list of environments, which can 
        be used to put the popped environments on again using a loop like for env in res: bcore.environment.push(env)
        @param until_size if positive, environments will be popped until the stack has the given size (i.e.
        length). In this case, the last popped environment will be returned. Must be smaller than the current
        stack size if larger than -1. Its valid to not pop anything if until_size == len(stack), mainly for
        convenience.
        """
        if until_size > -1:
            # Allow it to have equal size, to make usage easier
            assert until_size <= len(self), "can't pop if until_size is larger than our current size"
            res = list()
            while until_size != len(self):
                res.append(self.pop())
            # end while there are environments to pop
            return list(reversed(res))
        # end handle pop-until
        
        # don't count the base environment
        if len(self._stack) > 1:
            environment = self._stack.pop()
        else:
            environment = None
            raise ValueError("pop attempted on empty stack")
        #end keep one environment
        
        self._mark_rebuild_changed_context()
        return environment

    def reset(self, new_base=False):
        """ convenience method, clears the stack down to the base
            @param new_base : replace the base environment with a new empty one
        """
        if new_base:
            self._stack = [self._base_environment_type(BASE_IDENTIFIER)]
        else:
            self._stack = self._stack[0:1]
        # also clear the duplicate check registry
        self._mark_rebuild_changed_context()
        
    def replace(self, predicate, environment):
        """ search for an environment in the current stack (by name) and
            replace it with a new one
            @returns the environment that was replaced if it was found, else None
            @param predicate : p(env) => Bool a callable returning True if the given environment should be replaced
            @param environment : instance of an environment to replace with, or anything accepted by push()
        """
        environment_shadow_stack = list()
        old_env = None
        while len(self._stack) > 1:
            env = self._stack.pop()

            if predicate(env):
                self.push(environment)
                old_env = env
                break
            else:
                environment_shadow_stack.append(env)
            # end handle environment found
        # end while stack is large enough

        if old_env is None:
            log.warning("search and replace environment failed, environment matching predicate %s not found on the stack"
                            % str(predicate))
        # end print warning if replace-environment was not found
        
        self._stack.extend(reversed(environment_shadow_stack))
        self._mark_rebuild_changed_context()
        
        return old_env
        
    ## -- End Edit Interface -- @}
    
    # -------------------------
    ## @name Query Interface
    # @{
    
    def classes(self, interface):
        """@return a list of all registered plugin classes supporting the given interface
        """
        return self._walk_stack(self.RECURSE_ALWAYS, self._base_environment_type._classes, interface=interface)
    
    
    def services(self, interface, traversal_mode = RECURSE_UNTIL_FOUND, predicate = ServiceAll):
        """@return a list of services implementing \a interface, or an empty list.
            The obtained services are persistent, owned by an Environment and will keep their state as long
            as their environment is on the stack
            @param interface the interface to search for
            @param traversal_mode : controls stack traversal, see _walk_stack
            @param predicate function(service, interface) returning True for each service instance implementing 
            interface that should be returned (see predicate_foo in PREDICATES at the top if this file)
        """
        services = list()
        for service in self._walk_stack(traversal_mode, self._base_environment_type.services, interface=interface):
            if predicate(service, interface):
                services.append(service)
        # end for each service in stack
        
        return services
        
    ## -- End Query Interface -- @}
    
    # -------------------------
    ## @name Edit Interface
    # @{
    
    def new_services(self, interface, take_ownership = False, predicate = CreateAlways, args = None, kwargs = None):
        """Create services matching the given interface. Based on the amount of available prototypes, zero or 
        more services will be created.
        @return a list of zero or more newly created service instances
        @param interface a class each of the services needs to have implemented
        @param predicate controls creation of services implementing \a interface (see Createfoo in PREDICATES)
        It has the signature pred(cls, services, classes) => bool
        * cls = the candidate for instantiation
        * services = all created services so far, including the ones that already existed
        * classes = all found classes so far
        @param take_ownership if True, newly created services will be owned by the top-level environment, otherwise
        the caller is the only one keeping a pointer to them.
        @param args list of variable arguments for the constructor of cls, or None to indicate no arguments
        @param kwargs dictionary of keyword arguments for the constructor of cls, or None to indicate no kwargs
        @note take_ownership is off by default as more persistent services should be instantiated by the one 
        providing it, not by this method.
        """
        services = self.services(interface, traversal_mode = self.RECURSE_ALWAYS)
        classes = list()
        args = args or list()
        kwargs = kwargs or dict()
        for cls in self.classes(interface):
            if predicate(cls, services, classes):
                classes.append(cls)
                pv = cls._auto_register_instance
                cls._auto_register_instance = take_ownership
                try:
                    services.append(cls(*args, **kwargs))
                finally:
                    cls._auto_register_instance = pv
                # end handle value reset, no matter what
            # end if we found a class to instantiate
        # end for each class
        return services
        
    ## -- End Edit Interface -- @}
# end class EnvironmentStack


# ==============================================================================
## @name Helpers
# ------------------------------------------------------------------------------
# Convenience facilities to help writing plugins and interfaces for easy use of the environment architecture
## @{


# inherits from InterfaceMeta to support inheritance in the implements() function
class PluginMeta(bcore.MetaBase):
    """ metaclass for Plugin, registers the Plugin subclass in the current
        environment. Can be used with any type, doesn't need to derive from Plugin.
        However, the Plugin implementation will register instances, which the implementor would have to 
        do by himself otherwise."""
        
    ## See Plugin._stack
    _stack = None

    def __new__(mcls, name, bases, clsdict):
        """Registers the plugin's type to allow it to be instantiated""" 
        new_type = bcore.MetaBase.__new__(mcls, name, bases, clsdict)
        if name != 'Plugin' and new_type._auto_register_class:
            (mcls._stack or bcore.environment).register(new_type)
        # end exclude our own plugin marker (when type is instantated)
        return new_type
        

# end class PluginMeta

# Careful about renames: name is used verbatim in code above !
class Plugin(object):
    """ base class for all Plugins implementing interfaces """
    __metaclass__ = PluginMeta
    
    __slots__ = tuple()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Stack to use when handling service registration
    ## We try not to use global values to make it more testable
    _stack = None
    
    ## If True, new instances will automatically register themselves with the current Environment
    _auto_register_instance = True
    
    ## If True, any subclass of this type will be registered automatically with the current Environment
    _auto_register_class = True
    
    ## -- End Configuration -- @}
    
    
    def __new__(cls, *args, **kwargs):
        """ overloaded class creator, registers the instance in the current
            environment for all our instances """
        self = super(Plugin, cls).__new__(cls)
        if cls._auto_register_instance:
            (cls._stack or bcore.environment).register(self)
        # end handle registration
        return self
        
        
    # -------------------------
    ## @name Interface
    # @{
    
    ## Subclasses can set this variable to easily set their plugin name, which can be used for GUI purposes
    _plugin_name = None
    
    @classmethod
    def plugin_name(cls):
        """@return the name of the Plugin
        @note by default, we just create a name from the name of the class, unless _plugin_name is 
        set as member variable"""
        return cls._plugin_name or cls.__name__
    
    ## -- End Interface -- @}

# end class Plugin

## -- End Helpers -- @}

# ==============================================================================
## @name Module Loading
# ------------------------------------------------------------------------------
## @{

class PluginLoader(object):
    """ loads .py files from a given directory or load the given file, with recursion if desired
        @note equivalent pyc files will be used if available
        @note it just loads the .py files, including any non-component
        architecture code """
    __slots__ = (
                '_path',   # path at which to load plugins 
                '_recurse' # search for loadable plugins will be performed recursively
                )
        
    def __init__(self, path, recurse=False):
        self._path    = Path(path)
        self._recurse = recurse

    def _load_files(self, path, files):
        """ load all python \a files from \a path 
        @return list of loaded files as full paths"""
        res = list()
        for filename in filter(lambda x: re.search(r"\.py$", x), files):
            if filename.startswith('__'):
                continue
            py_file = os.sep.join([path, filename])
            (mod_name, _) = os.path.splitext(os.path.basename(py_file))
            try:
                self.load_file(py_file, mod_name)
            except Exception:
                # DEBUG: Just because if that happens, the logger doesn't output anything for some reason
                # TODO: fix the logger issue, traceback shouldn't be required
                import traceback
                traceback.print_exc()
                log.error("Failed to load %s from %s", mod_name, py_file, exc_info=True)
            else:
                log.info("loaded %s into module %s", py_file, mod_name)
                res.append(py_file)
            # end handle result
        # end for eahc file to load
        return res

    def load(self):
        """ perform the actual loading
        @return a list of files loaded successfully"""
        # if we should recurse, we just use the standard dirwalk.
        # we use topdown so top directories should be loaded before their
        # subdirectories and we follow symlinks, since it seems likely that's
        # what people will expect
        res = list()
        if self._path.isfile():
            res += self._load_files(self._path.dirname(), [self._path.basename()])
        else:
            for path, dirs, files in os.walk(self._path, topdown=True, followlinks=True):
                res += self._load_files(path, files)
                if not self._recurse:
                    break
                # end handle recursion
            # end for each directory to walk
        # end handle file or directory
        return res
        
    @classmethod
    def load_file(cls, python_file, module_name):
        """Load the contents of the given python file into a module of the given name.
        If the module is already loaded, it will be reloaded
        @return the loaded module object
        @throws Exception any exception raised when trying to load the module"""
        imp.load_source(module_name, python_file)
        return sys.modules[module_name]
        
# end class PluginLoader

## -- End Module Loading -- @}
