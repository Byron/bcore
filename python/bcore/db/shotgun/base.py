#-*-coding:utf-8-*-
"""
@package bcore.db.shotgun.base
@brief Implementations for use with the shotgun database

@copyright 2013 Sebastian Thiel
"""
__all__ = ['shotgun_schema', 'ProxyShotgunConnection', 'ProxyMeta']

import bcore
from .interfaces import IShotgunConnection
from bcore.core.component import EnvironmentStackContextClient
from bcore.core.kvstore import KeyValueStoreSchema
from bcore.utility import LazyMixin

from inspect import isroutine

# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

shotgun_schema = KeyValueStoreSchema('shotgun', {'host' : str,
                                                 'api_script' : str,
                                                 'api_key' : str,
                                                 'http_proxy' : str})


log = service(bcore.ILog).new('bcore.db.shotgun.base')


class ProxyMeta(IShotgunConnection.__metaclass__):
    """Redirect all calls as defined in first base class to the configured proxy member"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Member to which to redirect calls, such as getattr(self._proxy, name)(*args, **kwargs)
    proxy_class_attr = '_proxy_attr'
    
    ## An attribute with an iterable of names of read-only methods
    ## Subclasses may then implement them differently
    rw_methods_class_attr = '_rw_methods_'
    
    ## Class to use to obtain a list of methods to implement
    type_to_implement = IShotgunConnection 
    
    ## -- End Configuration -- @}
    
    
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    @classmethod
    def _create_method(cls, method_name, is_readonly, proxy_attr):
        """@return a new method named method_name that does not alter it's instance
        @note all additional arguments are mainly for your information
        @param cls this metaclass instance
        @param method_name name of method that is to be created
        @param is_readonly if True, the method must not change the underlying object
        @param proxy_attr the name of the attribute on instance that keeps the proxy instance."""
        def func(instance, *args, **kwargs):
            return getattr(getattr(instance, proxy_attr), method_name)(*args, **kwargs)
            
        func.__name__ = method_name
        return func
    
    ## -- End Subclass Interface -- @}
    
    def __new__(metacls, clsname, bases, clsdict):
        """Create a proxy-method for every method we have to re-implement if it is not overridden in the 
        derived class"""
        proxy_attr = metacls._class_attribute_value(clsdict, bases, metacls.proxy_class_attr)
        assert proxy_attr, "A proxy attribute must be set in member %s" % metacls.proxy_class_attr
        rw_method_names = metacls._class_attribute_value(clsdict, bases, metacls.rw_methods_class_attr) or tuple()
        
        for name, value in metacls.type_to_implement.__dict__.items():
            if not isroutine(value) or name in clsdict:
                continue
            # for now, just create a simple varargs method that allows everything
            # Could use new.code|new.function to do it dynamically, or make code to eval ... its overkill though
            clsdict[name] = metacls._create_method(name, name not in rw_method_names, proxy_attr)
        # end for each method to check for
        
        return super(ProxyMeta, metacls).__new__(metacls, clsname, bases, clsdict)

# end class ProxyMeta

## -- End Utilities -- @}


class PluginProxyMeta(ProxyMeta, Plugin.__metaclass__):
    """A MetaClass for Proxies and use with types that derive from Plugin.
    Such a type must redefine its __metaclass__ to use this one instead"""
    __slots__ = ()
    

# end class ProxyMetaPlugin



class ProxyShotgunConnection(IShotgunConnection, LazyMixin, EnvironmentStackContextClient):
    """Wraps an actual shotgun connection object and redirects all calls to it.
    
    It implements support for a proxy server
    """
    __slots__ = ('_proxy')
    __metaclass__ = ProxyMeta
    
    # -------------------------
    ## @name Configuration
    # @{
    
    _proxy_attr = '_proxy'
    _schema = shotgun_schema
    
    ## -- End Configuration -- @}

    def __init__(self, shotgun=None):
        """Intiialize ourselves with the given shotgun object
        @param shotgun if None, we will initialize the shotgun object on first access from our contexts connection
        information"""
        if shotgun:
            self._proxy = shotgun
        
    def _set_cache_(self, name):
        if name == '_proxy':
            connection_info = self.context_value()
            
            # delay import not to slow downloading of bcore !
            import shotgun_api3
            log.info("Connecting to Shotgun ...")
            self._proxy = shotgun_api3.Shotgun( connection_info.host, 
                                                connection_info.api_script,
                                                connection_info.api_key,
                                                http_proxy = connection_info.http_proxy or None
                                               )
            log.info("Shotgun connection established")
        else:
            super(ProxyShotgunConnection, self)._set_cache_(name)
        # end handle attribute name

# end class ProxyShotgunConnection

