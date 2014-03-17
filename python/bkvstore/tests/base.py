#-*-coding:utf-8-*-
"""
@package bcore.tests.kvstore.base
@brief base types which are shared among test modules in this package

@copyright 2012 Sebastian Thiel
"""
__all__ = ['TestConfigurationBase']

import yaml


from bcore.tests import TestCaseBase
from bcore.kvstore import OrderedDictYAMLLoader

class TestConfigurationBase(TestCaseBase):
    __slots__ = ()

    @classmethod
    def fixture_path(cls, name):
        """@return mrv path to the configuration fixture file"""
        return super(TestConfigurationBase, cls).fixture_path('core/config/' + name)
        
    @classmethod
    def config_data(cls, name):
        """@return deserialized yaml dictionary with data from the given file
        using the OrderedDictYAMLLoader"""
        return yaml.load(open(cls.fixture_path(name)), Loader = OrderedDictYAMLLoader)
        
# end class TestConfigurationBase

    
