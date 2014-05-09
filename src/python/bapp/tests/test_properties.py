#-*-coding:utf-8-*-
"""
@package bkvstore.tests.test_properties
@brief tests for bkvstore.properties

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

from .base import (TestCoreCaseBase,
                   with_application)
from bapp.properties import *
from bkvstore import RootKey
from butility import Path

from nose import SkipTest

## [ExampleContextClient]

class ExampleContextClient(PropertyApplicationSettingsMixin):
    __slots__ = ()
    
    site = CompoundPropertyDescriptor(ContextPropertyDescriptor(name='id', type=str),
                                      CompoundPropertyDescriptor(
                                            ContextPropertyDescriptor(name='repository', type=Path),
                                            name='root_path'
                                      ))

## [ExampleContextClient]
# end class ExampleContextClient


class TestEnvironmentProperties(TestCoreCaseBase):
    __slots__ = ()

    @with_application
    def test_base(self):
        """Test functionality of KVStore properties"""
        # raise SkipTest("TODO: Revision of this test once it's clear where the ContextClient is going, and properties of course")
        client = ExampleContextClient()
        assert client.settings_schema().key() == RootKey
        assert issubclass(client.settings_schema().site.id, str)
        
        assert not client.has_value_cache()
        assert client.clear_value_cache() is client, 'clear without having cache is no problem'
        assert client.value_cache(), "should have obtained some value"
        assert client.has_value_cache()
        client.clear_value_cache()
        assert not client.has_value_cache(), "shouldn't have value cache after clearing it"
        
        ## [ExampleContextClient Usage]
        assert len(client.site) == 2
        assert isinstance(client.site.id, str)
        assert isinstance(client.site.root_path.repository, Path)
        ## [ExampleContextClient Usage]
        
        assert client.has_value_cache(), "Properties auto-retrieve the cache"
