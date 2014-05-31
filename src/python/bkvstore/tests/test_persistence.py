#-*-coding:utf-8-*-
"""
@package bkvstore.tests.test_persistence
@brief tests for bkvstore.persistence

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = []

import yaml

from .base import TestConfiguration

# test * imports (could have defective '__all__')
from bkvstore.persistence import OrderedDictYAMLLoader
from butility import OrderedDict

class TestConfigurationCore(TestConfiguration):
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
            assert len(section) == 6
            isection = iter(section)
            assert next(isection) == 'string'
            assert next(isection) == 'int'
            assert next(isection) == 'float'
            assert next(isection) == 'list'
            assert next(isection) == 'subsection'
            section = section['subsection']
            assert len(section) == 2
            isection = iter(section)
            assert next(isection) == 'string'
        #end verify data
        verify_data(data)
        
        # stability of the data
        yaml_data = yaml.dump(data)
        data_duplicate = yaml.load(yaml_data, Loader = OrderedDictYAMLLoader)
        assert data_duplicate == data
        verify_data(data_duplicate)
        
