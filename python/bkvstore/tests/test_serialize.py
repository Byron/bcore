#-*-coding:utf-8-*-
"""
@package bcore.tests.kvstore.test_yaml
@brief Tests for bkvstore.yaml

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from bcore.tests.kvstore.base import TestConfigurationBase
from bcore.tests import with_rw_directory

# Test * import
from bkvstore import (
                                KeyValueStoreProviderDiffDelegate, 
                                RelaxedKeyValueStoreProviderDiffDelegate,
                                ChangeTrackingSerializingKeyValueStoreModifierBase,
                                YAMLStreamSerializer
                            )
from bkvstore.serialize import *
from bkvstore.persistence import OrderedDictYAMLLoader
from bcore.utility import tagged_file_paths

import yaml


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
    def fixture_path(cls, filename):
        """@return path to our own fixtures"""
        return super(TestYamlConfiguration, cls).fixture_path("test_yaml/%s" % filename)
        
    @classmethod
    def config_fixtures(cls, tag_list):
        """@return all configuration fixture paths which match the given tags"""
        return tagged_file_paths(cls.fixture_path(''), tag_list, '*.yaml')
        
    @with_rw_directory
    def test_yaml_modifier(self, rw_dir):
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
        
# end class TestYamlConfiguration
