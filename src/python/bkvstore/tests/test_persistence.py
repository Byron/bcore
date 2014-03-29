#-*-coding:utf-8-*-
"""
@package bkvstore.tests.test_persistence
@brief tests for bkvstore.persistence

@copyright 2012 Sebastian Thiel
"""
__all__ = []

import yaml

from .base import TestConfigurationBase

# test * imports (could have defective '__all__')
from bkvstore.persistence import OrderedDictYAMLLoader
from butility import OrderedDict

class TestConfigurationCore(TestConfigurationBase):
    __slots__ = ()

    def test_persistence(self):
        """figure out an in-python format that resembles an ini file, 
        with additional perks
        """
        # can serialization/deserialization of what we want to do is stable
        data = self.config_data('basic.yaml')
        # stability of the data
        yaml_data = yaml.dump(data)
        
        def verify_data(data):
            """chekc the contents of inbound data dict"""
            # verify data and order
            assert isinstance(data, OrderedDict)
            assert len(data) == 1
            section = data['section']
            assert isinstance(section, OrderedDict)
            assert len(section) == 5
            isection = iter(section)
            assert isection.next() == 'string'
            assert isection.next() == 'int'
            assert isection.next() == 'float'
            assert isection.next() == 'list'
            assert isection.next() == 'subsection'
            section = section['subsection']
            assert len(section) == 2
            isection = iter(section)
            assert isection.next() == 'string'
        #end verify data
        verify_data(data)
        
        # stability of the data
        yaml_data = yaml.dump(data)
        data_duplicate = yaml.load(yaml_data, Loader = OrderedDictYAMLLoader)
        assert data_duplicate == data
        verify_data(data_duplicate)
        
