#-*-coding:utf-8-*-
"""
@package bcore.db.shotgun.components.rwconnection
@brief A module with a connection that reads and writes from/to shotun

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from ..base import (
                        ProxyShotgunConnection,
                        PluginProxyMeta
                   )


class ProxyShotgunConnectionPlugin(ProxyShotgunConnection, Plugin):
    """Loads the ProxyShotgunConnection as Plugin"""
    __slots__ = ()
    __metaclass__ = PluginProxyMeta

# end class ProxyShotgunConnectionPlugin
