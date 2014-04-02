#-*-coding:utf-8-*-
"""
@package bkvstore.tests.base
@brief base types which are shared among test modules in this package

@copyright 2012 Sebastian Thiel
"""
__all__ = ['TestConfigurationBase']

import yaml


from butility.tests import TestCaseBase
from butility import Path
from bkvstore import OrderedDictYAMLLoader

class TestConfigurationBase(TestCaseBase):
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

    @classmethod
    def config_data(cls, name):
        """@return deserialized yaml dictionary with data from the given file
        using the OrderedDictYAMLLoader"""
        return yaml.load(open(cls.fixture_path(name)), Loader = OrderedDictYAMLLoader)
        
# end class TestConfigurationBase

    
