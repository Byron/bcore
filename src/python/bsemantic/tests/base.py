#-*-coding:utf-8-*-
"""
@package bsemantic.tests.base
@brief Contains some base types used by many test cases

@copyright 2012 Sebastian Thiel
"""
__all__ = ['TestBase']

from bcore.tests import TestCaseBase
from bcore.utility import DictObject

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
#end obtain fast loader if possible

from bcore.path import Path


class TestBase(TestCaseBase):
    __slots__ = ()
    
    # -------------------------
    ## @name Fixtures
    # @{
    
    path_rules_file = 'path_rules.yaml'
    
    # some fundamental data set we use multiple times. Must be copied
    fs_root = '/mnt/projects'
    _base_data = DictObject(dict(project = DictObject(dict(
                                                root_path = DictObject(
                                                                        dict(fs_absolute = fs_root))
                                                                      )
                                             )
                           ))
        
    ## -- End Fixtures -- @}
    
    @classmethod
    def base_data(cls):
        """@return a copy of our basic data set as dict_object"""
        return DictObject(cls._base_data.to_dict())
    
    @classmethod
    def rule_data(cls, name):
        """a nested dictionary representing ruleset data, it was parsed from a file of the given name"""
        return yaml.load(open(cls.fixture_path(name)), Loader=Loader)
        
    @classmethod
    def setUpClass(cls):
        """Initialize some shared members"""
        cls.path_rule_data = cls.rule_data(cls.path_rules_file)


# end class TestBase
