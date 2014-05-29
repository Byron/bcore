#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_utility
@brief tests for bprocess

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from butility.tests import ( TestCase,
                             with_rw_directory)
import bapp
from bapp import preserve_application
from butility import (wraps,
                      Path)
from bkvstore import KeyValueStoreModifier
from bapp.tests import with_application

# test from * import
from bprocess.utility import *


def with_application(fun):
    """A decorator which assures that our particular test configuration is loaded specifically, without
    traversing the hiararchy in order to not be dependent on whatever assembly we are in
    @note does not load plugins based on package information"""
    @wraps(fun)
    def wrapper(*args, **kwargs):
        app = bapp.Application.new(settings_trees=Path(__file__).dirname() / 'etc', 
                                   settings_hierarchy=False,
                                   user_settings=False)
        return fun(*args, **kwargs)
    # end wrapper

    return wrapper


class TestUtilities(TestCase):
    """Test process controller utiltiies"""
    __slots__ = ()
    
    @preserve_application
    @with_application
    @with_rw_directory
    def test_base(self, rw_dir):
        """test fundamentals"""
        
        class TestPackageTracker(PackageMetaDataChangeTracker):
            def _initial_settings_value(self):
                """copy of initial context"""
                if not hasattr(self, 'kvstore'):
                    self.kvstore = KeyValueStoreModifier(super(TestPackageTracker, self)._initial_settings_value())
                # end initialize our cache
                return self.kvstore._data()
                
            def _settings_path(self):
                return rw_dir / 'package-settings.json'
        #end class
        
        tracker = TestPackageTracker('nosetests')
        assert tracker.package_name() == 'nosetests'
        assert not tracker.changes(), "the first time, there should be no change"
        
        assert tracker.make_package_state_current() is tracker
        assert not tracker.changes(), "after remembering, there should be no change, still"
        
        
        for previous in range(2):
            assert len(tracker.package_data(previous)), 'should have iterated at least one package'
            assert len(list(tracker.iter_package_data(previous)))
        # end for each 'previous' state
        
        
        # make changes
        tracker.reset()
        packages = tracker.settings_value(tracker.kvstore)
        # This will changes the current state
        packages.nosetests.version = '5.0'
        packages.nosetests.url = 'foo.bar'
        tracker.kvstore.set_value_by_schema(tracker.settings_schema(), packages)
        
        # This will be the previous state
        changes = tracker.changes()
        assert len(changes.packages) == 1
        assert changes.packages.nosetests.url == ''
        assert changes.packages.nosetests.version == 'unknown'
        
        tracker._settings_path().remove()
        assert not tracker.package_data(previous=True), "if there is no package data, there is no data"

