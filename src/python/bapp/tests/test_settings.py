#-*-coding:utf-8-*-
"""
@package bapp.tests.test_settings
@brief tests for bapp.settings

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
from butility.future import str


__all__ = []

import bapp
from .base import with_application
from butility.tests import (TestCase,
                            with_rw_directory)

# try * import
from bapp.settings import *
from butility import OrderedDict
from bkvstore import (KeyValueStoreSchema,
                      RootKey)


class TestSettingsClient(PersistentApplicationSettingsMixin):
    """A client with a simple schema to test out its settings"""
    __slots__ = ('_settings_dir')
    
    _schema = KeyValueStoreSchema('dog', dict(name=str,
                                              meal=str,
                                              friends = list(),
                                              location = dict(x=float, y=float)))
    
    settings_id = lambda self: 'dog'
    
    def __init__(self, settings_dir):
        self._settings_dir = settings_dir
        
    def _settings_path(self):
        return self._settings_dir / PersistentSettings.StreamSerializerType.file_extension
    
    def set_values(self):
        """set some values for serialization"""
        dog = self.settings()
        dog.name = 'roofus'
        dog.meal = 'bone'
        dog.friends = ['cat', 'bunny']
        dog.location.x = 1.0
        dog.location.y = 2.0
        
        self.save_settings()
        
    def assert_values(self):
        """Checek values"""
        dog = self.settings()
        assert dog.name == 'roofus'
        assert dog.meal == 'bone'
        assert dog.friends == ['cat', 'bunny']
        assert dog.location.x == 1.0
        assert dog.location.y == 2.0

# end class TestSettingsClient


class TestSettings(TestCase):
    __slots__ = ()

    @with_rw_directory
    @with_application
    def test_settings(self, rw_dir):
        """Tests for settings and JSon serializer in the same moment"""
        target = rw_dir / 'foo' + PersistentSettings.StreamSerializerType.file_extension
        assert not target.isfile()
        schema_dict = OrderedDict()
        schema = KeyValueStoreSchema(RootKey, { 'foo' : dict(baz = int,
                                                             foz = float,),
                                                 'bar' : str,
                                                 'ordered' : list,})
        
        data = OrderedDict({ 'foo' : OrderedDict(dict(baz = 5, foz = 4.0)),
                             'bar' : 'hello',
                             'ordered' : [1, 2]}) 
        
        # Data could come from an actual kvstore if we like
        settings = PersistentSettings(data, target, take_ownership = False)
        data.bar = 5
        assert settings.data().bar != data.bar, 'should have made a copy'
        settings_data = settings.value_by_schema(schema)
        data.bar = 'hello'
        assert settings_data.bar == data.bar
        assert settings_data.ordered == data.ordered
        
        settings_data.bar = 5
        settings_data.foo.baz = 10  # note the incorrect type ! Its tranformed to a string
        settings_data.ordered = [3, 4, 5]
        
        settings.set_value_by_schema(schema, settings_data)
        assert settings.changes()
        assert 'foz' not in settings.changes().foo
        assert settings.save_changes(open(target, 'w')) is settings, "It should be easy to save changes"
        assert settings.settings_data(open(target, 'r')), "should have something to work with"
        settings_data = settings.value_by_schema(schema)
        
        prev_size = target.stat().st_size
        assert target.isfile() and prev_size, "Should have created file by now"
        
        # changes should still be there, and file should be identical
        assert settings.changes() and settings.save_changes(open(target, 'w'))
        assert target.stat().st_size == prev_size
        
        
        
        # Now we pretend to be a in a new session and want to reload our settings
        new_settings = PersistentSettings(data, target, take_ownership = False)
        new_settings_data = new_settings.value_by_schema(schema)
        # NOTE: order is lost when diffing ! we use sets there ... . For now no problem
        # assert new_settings_data == settings_data
        assert new_settings_data.foo.baz == settings_data.foo.baz
        assert new_settings_data.bar == settings_data.bar
        assert new_settings_data.ordered == settings_data.ordered
        
        # Changes should be equivalent
        nsc = new_settings.changes()
        osc = settings.changes()
        assert set(nsc.keys()) == set(osc.keys()), "Order seems to change, but not the contents"
        assert nsc.foo == osc.foo
        assert nsc.bar == osc.bar
        assert nsc.ordered == osc.ordered
        
        # Now, instead of a space save, do a full one, which will cause all data to be written unconditionally.
        # This will forever override every base value
        settings.save_changes(open(target, 'w'), sparse=False)
        assert target.stat().st_size > prev_size
        
        # When reading it back, it should still be exactly the same, except that we will never see changes coming
        # through from the base
        new_settings = PersistentSettings(data, target, take_ownership = False)
        # we faithfully assume the other fields match as well
        assert new_settings.changes().ordered == settings.changes().ordered
        
    @with_rw_directory
    @with_application
    def test_client(self, rw_dir):
        """Test settings client"""
        client = TestSettingsClient(rw_dir)
        client.set_values()

        other_client = TestSettingsClient(rw_dir)
        other_client.assert_values()
        
        
