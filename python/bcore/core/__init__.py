#-*-coding:utf-8-*-
"""
@package tx.core
@brief Acts as a category for all core functionality that should always be available

Generally, all submodules should be imported. Sub-Packages should be imported just by the client.

@copyright 2012 Sebastian Thiel
"""

def _init_component_framework():
    """Assure the component framework is available"""
    from . import component
    component.initialize()
    
def initialize():
    """Initialize the core and all its functionality"""
    _init_component_framework()
    
    
