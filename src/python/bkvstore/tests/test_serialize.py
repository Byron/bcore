#-*-coding:utf-8-*-
"""
@package bkvstore.tests.test_yaml
@brief Tests for bkvstore.yaml

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import yaml

from .base import TestConfigurationBase
from butility.tests import with_rw_directory

from bkvstore import ( KeyValueStoreProviderDiffDelegate,
                       RelaxedKeyValueStoreProviderDiffDelegate,
                       ChangeTrackingSerializingKeyValueStoreModifierBase,
                       YAMLStreamSerializer )
from bkvstore.serialize import *
from bkvstore.persistence import OrderedDictYAMLLoader
from bkvstore.types import YAMLKeyValueStoreModifier
from butility import tagged_file_paths



# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
# Used to get loose kvstore semantics back for those relatively old tests
## @{

class LooseYAMLKeyValueStoreModifier(ChangeTrackingSerializingKeyValueStoreModifierBase):
    """Loose semantics"""
    __slots__ = ()
    
    DiffProviderDelegateType = RelaxedKeyValueStoreProviderDiffDelegate
    StreamSerializerType = YAMLStreamSerializer
    
# end class LooseYAMLKeyValueStoreModifier

## -- End Utilities -- @}



class TestYamlConfiguration(TestConfigurationBase):
    __slots__ = ()
    
    @classmethod
    def config_fixtures(cls, tag_list):
        """@return all configuration fixture paths which match the given tags"""
        return tagged_file_paths(cls.fixture_path(''), tag_list, '*.yaml')
        
    @with_rw_directory
    def __test_yaml_modifier(self, rw_dir):
        """Verify only the changes are written back
        @todo when diffing anything, the order of keys gets messed up (after set_value), probably because of the merge
        However, lets just move on for now.
        """
        delta_file = rw_dir / "userconfig.yaml"
        tags = ('lnx', 'maya')
        
        assert not delta_file.isfile(), "delta file shouldn't exist yet"
        input_files = self.config_fixtures(tags)
        assert input_files, "Should have gotten some fixtures"
        
        # see how it deal with strings as input (should convert to Path)
        cmod = LooseYAMLKeyValueStoreModifier(input_files + [delta_file]) # yet we add it, there should be no error
        
        assert len(cmod.input_paths()) == len(tuple(input_files)) + 1
        
        # can use the config right away - just a few checks
        assert cmod.value('platform', dict()).path_separator == "/", "Should have linux platform separator"
        key = 'paths'
        paths = cmod.value(key, dict())
        assert paths.cache_root.fs_path == "/CACHE/JOBS"
        
        # if there are no changes, no file is written
        #############################################
        assert not cmod.changes(), "should not have changes yet"
        assert not delta_file.isfile(), "File should not yet exist"
        cmod.save_changes(open(delta_file, 'w'))
        assert delta_file.stat().st_size == 0, "File should still not be there"
        
        # MAKE CHANGES
        ################
        # make a change, and reload - this is already tested by the test_base, so its just a quick check here
        new_val = "/SOMETHING"
        paths.cache_root.fs_path = new_val
        paths.cache_root.new_info = 42
        
        assert cmod.set_value(key, paths).value(key, dict()).to_dict() == paths.to_dict()
        assert cmod.value(key, dict()) != paths 
        
        assert cmod.reload().value(key, dict()) == paths
        
        # save the changes, only our single change should be written
        changes = cmod.changes()
        assert changes
        cmod.save_changes(open(delta_file, 'w'))
        assert yaml.load(open(delta_file)) == changes
        assert cmod.changes(), "should still have changes after saving them"
        
        assert len(changes.paths.cache_root) == 2, "Expected two changed items"
        
        # assure that the changes will be read back in automatically
        cmod = LooseYAMLKeyValueStoreModifier(input_files)
        assert not cmod.changes(), "reload and changes are gone"
        
        # re-apply the changes actively
        cmod.load_changes(open(delta_file))
        assert cmod.value(key, dict()).cache_root.fs_path == new_val, "Expected changes to be reloaded"
        assert cmod.changes(), "changes have been read back from input files which also contains target file"
        
        
        # reloading with a changed set of files works as well
        cmod.reload(self.config_fixtures(('win', 'maya')))
        paths = cmod.value(key, dict())
        assert paths.project_root.fs_path == "P:\\JOBS", "Should have windows config"
        assert paths.cache_root.fs_path == "/SOMETHING", "Should still have my changes applied"

    def test_yaml_merge(self):
        """Assert that horizontal yaml merging works as expected"""
        basic = self.fixture_path('basic.yaml')
        basic_ovr = self.fixture_path('basic_overrides.yaml')

        # paths and open files can be used
        store = YAMLKeyValueStoreModifier((basic, open(basic_ovr, 'rb')))
        d = store.data()
        assert d.section.string == 'newvalue', "Simple scalar override didn't turn out as expected"
        assert isinstance(d.section.int, dict), "Should have overridden a scalar with a tree"
        assert d.section.int.foo == 1 and d.section.int.bar == 2, "expected particular tree values"

        assert d.section.list == ['item5', 'item4', 'item3', 'item2', 'item1']
        assert d.section.subsection is not None, "subsection shouldn't be overridden by None"
        assert isinstance(d.section.other_tree, dict), "Can't override a complex value with a scalar in additive mode"


        # The inverse will have an inverse effect - order matters, of course
        store = YAMLKeyValueStoreModifier((basic_ovr, basic))
        d = store.data()
        assert d.section.string == 'value'
        assert isinstance(d.section.int, dict)
        assert d.section.list == ['item3', 'item2', 'item1', 'item5', 'item4']
        assert isinstance(d.section.other_tree, dict)
            

        err_indent = self.fixture_path('with_error/invalid_indent.yaml')
        inexistent = 'clearly/doesn_t/exist'
        store = YAMLKeyValueStoreModifier((basic, err_indent, inexistent))

        assert store.data() == YAMLKeyValueStoreModifier((basic, )).data(), "invalid files shouldn't affect the outcome, but be ignored"
        
        
# end class TestYamlConfiguration
