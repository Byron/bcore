#=-*-coding:utf-8-*-
"""
@package bcontext.base
@brief implements an adjustable context, coming with implementation and configuration

@copyright 2012 Sebastian Thiel
"""
__all__ = ['Context', 'ContextStack',
           'StackAutoResolveAdditiveMergeDelegate']

import re
import logging

from butility import ( OrderedDict,
                       LazyMixin,
                       InterfaceBase,
                       MetaBase,
                       Error,
                       Path )

from bdiff import ( NoValue,
                    TwoWayDiff,
                    AutoResolveAdditiveMergeDelegate )

from bkvstore import ( KeyValueStoreSchemaValidator,
                       KeyValueStoreModifier,
                       KeyValueStoreSchema,
                       RootKey )

from .utility import ContextStackClient

log = logging.getLogger(__name__)



# ==============================================================================
## @name Constants
# ------------------------------------------------------------------------------
## @{

## identifier for the base Context on the stack and
## the category name for contexts that do not set their own
BASE_IDENTIFIER = "$base$"

## -- End Constants -- @}


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class ContextStackClient(InterfaceBase):
    """Base implementation to allow anyone to safely use the context of the global Context stack.
    Everyone using the global context should derive from it to facilitate context usage and to allow the 
    ContextStack to verify its data.
    
    This type basically brings together a schema with another type, to make data access to any context easy
    """
    __slots__ = ()

    ## Schema specifying how we would like to access the global Context context 
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
    def kvstore_value(cls, context, resolve=True):
        """@return a nested dict with getattr access as obtained from the current ContextStack's context, 
        validated against our schema.
        @param cls
        @param context if not None, use the given context (KeyValueStoreProvider) instead of the global one
        @param resolve if True, string values will be resolved
        @note use this method when you need access to the datastructure matching your schema"""
        schema = cls.schema()
        return context.value(schema.key(), schema, resolve=resolve)
        
# end class ContextStackClient


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


## -- End Utilities -- @}



class Context(object):
    """ A context is defined by its kvstore, holding configuration values, and a list of service instances or 
    types. A service is an implementation of a particlar interface, by which it may be retrieved or instantiated.

    Each Context has a name and a category, which helps to further distinguish it.

    A Context maintains a strong pointer to all Plugin instances by default.
    """
    __slots__ = (
                    '_name',     # name of the Context
                    '_registry', # a list of instances and types 
                    '_kvstore'   # the contexts context as kvstore
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## it's possible to find contexts by category
    ## Subclasses can override it
    _category = BASE_IDENTIFIER
    
    ## Type used to instantiate a kv store modifier
    KeyValueStoreModifierType = KeyValueStoreModifier
    
    ## -- End Configuration -- @}

    
    def __init__(self, name):
        """ @param name of this context"""
        self._name  = name
        self.reset()
        
    def __repr__(self):
        return "Context('%s')" % (self._name)

    # -------------------------
    ## @name Utilities
    # @{
    
    def _filter_registry(self, interface, predicate):
        """Iterate the registry and return a list of matching items, but only consider registrees for which 
        predicate(item) returns True"""
        items = list()
        # Items that came later will be used first - this way items that came later can override newer ones
        for item in reversed(self._registry):
            if (isinstance(item, interface) or (isinstance(item, type) and issubclass(item, interface))) \
            and predicate(item):
                items.append(item)
            # end if registree is suitable
        # end for each registered item
        return items
    
    def _contents_str(self):
        """Display the contents of the Context primarily for debugging purposes
        @return string indicating the human-readable contents
        @todo: revise printing"""
        otp = str(self)
        otp += "\t* registered services|types:\n"
        for item in self._registry:
            otp += "\t%s\n" % item
            # Could list supported interfaces here
        otp += "\t* store:\n"
        otp += re.sub(r"(^|\n)", r"\1\t", str(self._kvstore)) + '\n'
        return otp

    def _context(self):
        """@returns a our context
        @note changes to it will be reflected in the Context"""
        return self._kvstore
        
    def _register(self, plugin):
        """ register an instantiated plugin or a type
            @param plugin : the plugin instance to register or the class to use for instantiation
            @note we are save and will not add duplicates to the registry 
            @return self
        """
        if plugin not in self._registry:
            self._registry.append(plugin)
        return self
        
    ## -- End Utilities -- @}
        
    # -------------------------
    ## @name Attributes
    # Simple attributes to categorize the Context
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

    def classes(self, interface, predicate = lambda cls: True):
        """@return all classes implementing \a interface
        @param interface the interface to search for
        @param predicate f(cls) => Bool, return True for each class supporting the interface 
        you want to have returned
        """
        return self._filter_registry(interface, lambda x: isinstance(x, type) and predicate(x))
    
    def services(self, interface, predicate = lambda service: True):
        """@return all services (i.e. instances) implementing \a interface
        @param interface the interface to search for
        @param predicate f(service) => Bool, return True for each service having the interface 
        you want to have returned
        """
        return self._filter_registry(interface, lambda x: not isinstance(x, type) and predicate(x))
        
    ## -- End Query Interface -- @}

    # -------------------------
    ## @name Edit Interface
    # @{
            
    def reset(self):
        """ we forget all our classes and services, as well as our context"""
        self._kvstore = self.KeyValueStoreModifierType(OrderedDict())
        self._registry = list()
        
    ## -- End Edit Interface -- @}

# end class Context


class ContextStack(LazyMixin):
    """ Keeps a stack of Context instances.
        returns services (instances of Plugins) or types for instantiation by searching through this stack
        registers services in the current Context.
        Will always have (and keep) a base Context that serves as 'catch all' Context.
    """
    __metaclass__ = MetaBase
    __slots__ = (   
                    '_stack',                               # multiple context instances
                    '_kvstore',                             # a cached and combined kvstore
                    '_num_aggregated_kvstores'              # number contexts aggregated in our current cache
                )
    
    # -------------------------
    ## @name Configuration
    # @{

    ContextType = Context
    
    ## -- End Configuration -- @}

    def __init__(self):
        self._stack = list() # the stack itself
        self.reset()
        
    def _set_cache_(self, name):
        if name == '_kvstore':
            self._kvstore = self._aggregated_kvstore()
        else:
            return super(ContextStack, self)._set_cache_(name)
        # end handle cache name

    def __str__(self):
        return '\n'.join(str(ctx) for ctx in reversed(self._stack))
    
    def _contents_str(self):
        """ print a comprehensive representation of the stack 
            @todo convert this into returning a data structure which would be useful and printable            
        """
        otp = str()
        for idx, env in enumerate(self._stack):
            otp += "### Context %i - %s ###############\n\n" % (idx, env.name())
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
        self._num_aggregated_kvstores = 0
        
    def register(self, plugin):
        """registers plugin as a service providing all interfaces it derives from
            @param plugin any instance or class  
        """
        self.top()._register(plugin)
        
    # -------------------------
    ## @name Protocols
    # @{
    
    def __len__(self):
        """@return the length of the Context stack """
        return len(self._stack)
    
    ## -- End Protocols -- @}
    
    # -------------------------
    # Internal Query Interface
    #
    
    def _aggregated_kvstore(self, aggregated_base=None, start_at = 0):
        """@return new context as aggregate of all contexts on our stack, bottom up"""
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
        # end for each Context
        self._num_aggregated_kvstores = len(self._stack)

        res = delegate.result()
        if res is NoValue:
            assert aggregated_base is not None
            assert isinstance(aggregated_base, OrderedDict)
            res = aggregated_base
        # end handle special case with empty dicts
        return self.ContextType.KeyValueStoreModifierType(res)
        
    # -- End Internal Query Interface --
    
    # -------------------------
    ## @name Query Interface
    # @{
    
    def kvstore(self):
        """@return aggreated kvstore of the entire Context stack, representing a combination of all
        of their kvstore data
         """
        kvstore = self._kvstore

        # Check if we still have to add some contexts, as someone pushed in the meanwhile
        if self._num_aggregated_kvstores != len(self._stack):
            kvstore = self._kvstore = self._aggregated_kvstore(kvstore._data(), self._num_aggregated_kvstores)
        # end update kvstore

        return kvstore
    
    def top(self):
        """@return the Context on the top of stack """
        return self._stack[-1]
    
    def schema_validator(self):
        """@return a KeyValueStoreSchemaValidator instance initialized with all our Context's schemas 
        as well as registered ContextStackClient services to allow schema and context validation"""
        validator = self._KeyValueStoreValidatorType()
        # bottom up - later contexts override earlier ones
        for ctx in self._stack:
            if hasattr()
            validator.append(ctx.schema())
            # Context returns services newest first, which is something we hereby undo to allow
            # proper schema merging.
            for client in reversed(ctx.services(ContextStackClient)):
                schema = client.schema()
                if schema not in validator:
                    validator.append(schema)
                # end append schema exclusively
            # end for each client instance
        # end for each envrionments
        return validator
        
    def stack(self):
        """@return our Context stack
        @note not for general use, as you should not try to find individual Context instances. It can 
        be useful for closely bonded functions that whish to temporarily alter the stack though"""
        return self._stack
        
    ## -- End Query Interface -- @}
    
    # -------------------------
    ## @name Edit Interface
    # @{
    
    def push(self, context):
        """ push a context on to the stack
        @param context if string, push newly created empty Context with string as name.
        Otherwise, the context instance will be pushed.
        @return pushed context instance
        """
        if isinstance(context, basestring):
            context = self.ContextType(context)
        # end handle string contexts
        self._stack.append(context)
        return context

    def pop(self, until_size = -1):
        """@return top of stack Context after popping it off
        If until_size is larger -1, return value will be a correctly sorted list of contexts, which can 
        be used to put the popped contexts on again
        @param until_size if positive, contexts will be popped until the stack has the given size (i.e.
        length). In this case, the last popped context will be returned. Must be smaller than the current
        stack size if larger than -1. Its valid to not pop anything if until_size == len(stack), mainly for
        convenience.
        @note does not allow the base Context to be removed
        """
        if until_size > -1:
            # Allow it to have equal size, to make usage easier
            assert until_size <= len(self), "can't pop if until_size is larger than our current size"
            assert until_size > 0, "can't pop base context"
            res = list()
            while until_size != len(self):
                res.append(self.pop())
            # end while there are contexts to pop
        else:
            # don't count the base Context
            assert len(self._stack) - 1 > 0, "pop attempted on empty stack - base context wasn't counted"
            res = self._stack.pop()
        # end handle pop-until
        
        if res:
            self._mark_rebuild_changed_context()
        # end assure we handle no-pop scenario with until_size == len(self._stack)
        return res

    def reset(self, context = None):
        """clears the stack, keeping just a single instance of the given type
        @param context if not None, the Context instance to use as default base context.
        Otherwise a new default one will be created
        @return self
        """
        context = context or self.ContextType(BASE_IDENTIFIER)
        self._stack = [context]
        self._mark_rebuild_changed_context()
        return self

    ## -- End Edit Interface -- @}
    
    # -------------------------
    ## @name Query Interface
    # @{
    
    def classes(self, interface, predicate = lambda cls: True):
        """@return a list of all registered plugin classes supporting the given interface
        @param predicate f(service) => Bool, returns True for each class implementing
        interface that should be returned
        """
        res = list()
        for ctx in reversed(self._stack):
            res += ctx.classes(interface, predicate)
        # end for each context
        return res
    
    def services(self, interface, predicate = lambda service: True, find_all = False):
        """@return a list of services implementing \a interface, or an empty list.
        The obtained services are persistent, owned by one of our contexts and will keep their state as long as their context is on the stack
        @param interface the interface a service must implement
        @param find_all if False, you will only get the first matching service.
        Otherwise you will get all of them. The order is most suitable first.
        @param predicate f(service) => Bool, returns True for each service instance implementing
        interface that should be returned
        """
        services = list()
        for ctx in reversed(self._stack):
            services += ctx.services(interface=interface, predicate):
            if not find_all:
                break
            # end abort search early
        # end for each context
        return services
        
    ## -- End Query Interface -- @}
    
    # -------------------------
    ## @name Edit Interface
    # @{
    
    def new_services(self, interface,
                     maycreate = lambda cls, services, classes: True, 
                     take_ownership = False,
                     args = list(), kwargs = dict()):
        """Create services matching the given interface. For each available matching class in our registry, 
        a service (i.e. instance) will be created.
        @return a list of zero or more newly created service instances
        @param interface a class each of the services needs to have implemented
        @note take_ownership is off by default as more persistent services should be instantiated by the one 
        providing it, not by this method.
        @param maycreate controls creation of services implementing \a interface
        It has the signature pred(cls, services, classes) => bool
        * cls = the candidate for instantiation
        * services = all created services so far, including the ones that already existed
        * classes = all found classes so far
        @param take_ownership if True, newly created services will be owned by the top-level Context, otherwise
        the caller is the only one referencing to them.
        @param args list of variable arguments for the constructor of cls, or None to indicate no arguments
        @param kwargs dictionary of keyword arguments for the constructor of cls, or None to indicate no kwargs
        """
        services = self.services(interface, find_all = True)
        classes = list()
        args = args or list()
        kwargs = kwargs or dict()
        for cls in self.classes(interface):
            if maycreate(cls, services, classes):
                classes.append(cls)
                if hasattr(cls, '_auto_register_instance'):
                    pv = cls._auto_register_instance
                    cls._auto_register_instance = take_ownership
                # end handle auto-register
                try:
                    services.append(cls(*args, **kwargs))
                finally:
                    if hasattr(cls, '_auto_register_instance'):
                        cls._auto_register_instance = pv
                    # end handle auto-register
                # end handle value reset, no matter what
            # end if we found a class to instantiate
        # end for each class
        return services
        
    ## -- End Edit Interface -- @}
# end class ContextStack

