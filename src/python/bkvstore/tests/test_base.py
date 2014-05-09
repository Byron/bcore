#-*-coding:utf-8-*-
"""
@package bkvstore.tests.test_base
@brief tests for bkvstore.base

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import logging
from copy import deepcopy

from .base import TestConfigurationBase
from butility import (OrderedDict,
                      Version,
                      Path)

from bkvstore import *

from bdiff import (TwoWayDiff,
                   AdditiveMergeDelegate,
                   RootKey,
                   NoValue )
from bkvstore.diff import (KeyValueStoreModifierDiffDelegate,
                           RelaxedKeyValueStoreProviderDiffDelegate )


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class LooseKeyValueStoreProvider(KeyValueStoreProvider):
    """A provider with 'loose' semantics"""
    __slots__ = ()
    DiffProviderDelegateType = RelaxedKeyValueStoreProviderDiffDelegate

# end class LooseKeyValueStoreProvider


class LooseKeyValueStoreModifier(KeyValueStoreModifier):
    """A modifier using a loose delgate"""
    __slots__ = ()
    DiffProviderDelegateType = RelaxedKeyValueStoreProviderDiffDelegate
    
# end class LooseKeyValueStoreModifier


## -- End Utilities -- @}


class TestKeyValueStoreProvider(TestConfigurationBase):
    __slots__ = ()
    
    def _assert_cp_interface_simple(self, config_provider_type):
        """Verify value retrieval works with simple, non-nested values, and its interface"""
        data = self.config_data('basic.yaml')
        cps = config_provider_type(data, take_ownership=False)
        
        # verify input data
        assert cps._data() is not data, "it should copy the data"
        assert cps._data() == data, "It should copy, but not modify the data"
        
        assert config_provider_type(data, take_ownership=True)._data() is data, "It should have taken ownership"
        
        defval = 'default'
        assert cps.value('doesnt_exist', defval) is defval, "Expected default value if a key could not be found"
        assert not cps.has_value('doesnt_exist'), "Value shouldn't exist, not after making it the default"
        self.failUnless(cps.value('section.doesnt_exist', defval) is defval,
                            "Need default value if a key could not be found in section")
        # SH: None should be allowed, it could be what the user wants to store, and there's NoValue for marking
        #     something as having no value instead of None
        #self.failUnlessRaises(NoSuchKeyError, cps.value, 'doesnt_exist', None)
        
        assert cps.value('section.string', 'doesntmatter') == 'value', "Expected a key-hit as value exists"
        assert cps.value('section.int', 50) == 42, "integers should work similarly and come out in proper type"
        assert cps.has_value('section.int'), "Should actually have the value"
        assert len(cps.keys()) == 1, "exepected exactly one top-level key"
        # try non-existing base key
        assert len(cps.keys('doesnt.exist')) == 0, "nonexisting key should return empty list"
        assert len(cps.keys('section')) == 6, "Should have 6 keys in section"
        assert isinstance(cps.value('section.int', 50.0), float), "typecast should have been done automatically"
        
    def _assert_cp_interface_nested(self, config_provider_type):
        """Verify value retrieval works with simple, non-nested values, and its interface"""
        data = self.config_data('basic.yaml')
        default = deepcopy(data)      # we can go on with the dict, as the provider needs to copy it
        
        # SETUP DATA STRUCTURES
        ########################
        # default has more data
        s_name = 'section'
        subs_name = 'subsection'
        del(data[s_name]['list'])
        del(data[s_name][subs_name]['string'])
        
        # but data has another member as well
        tlo = 'toplevel_option'
        tlo_val = 'great'       # toplevel value
        ns_immutable_val = (1, 2, 3)        # new section immutable value
        ns_mutable_val = (1, [2, 3], 4)      # new section mutable value
        ns_name = 'newsection'
        data[s_name].setdefault(ns_name, dict())['value'] = ns_immutable_val
        data[s_name][ns_name]['mutable'] = ns_mutable_val
        data[tlo] = tlo_val
        
        # VERIFY DATA-STRUCTURES
        #########################
        cps = config_provider_type(data)
        assert cps._data is not data
        
        assert cps.value(tlo, 5) == 5, "If the type doesn't match, we get the default"
        assert cps.value(tlo, '') == tlo_val, "If the type matches, and we have a config value, we get it"
        
        # now we get a composed value
        val = cps.value(s_name, default[s_name])
        assert 'item3' in val['list'], "list key should have been added from default"
        assert 'string' in val[subs_name], "Should have 'string' in subsection from default"
        self.failUnless(val[ns_name]['value'] is ns_immutable_val, 
                        "Should have non-copy of new value, its not in default, but immutable")
        new_mutable_val = val[ns_name]['mutable']
        assert new_mutable_val == ns_mutable_val, "Expected equal mutable value"
        assert new_mutable_val is not ns_mutable_val, "Expected a copy of a mutable value"
        
    def _assert_cm_interface_simple(self, config_modifier_type):
        """Verify that we can deal with simple-non-nested values, by interface"""
        cmod = config_modifier_type(self.config_data('basic.yaml'))
        
        # set simple values
        n_key = 'new_option'            # new key
        n_val = 'new_option_value'      # new key's value
        key_count = len(cmod.keys())
        assert cmod.set_value(n_key, n_val).value(n_key, n_val * 2) == n_val, "Should have gotten value that I put in"
        assert len(cmod.keys()) == key_count + 1
        assert cmod.delete_value(n_key).value(n_key, 40) == 40, "Deleting a value should work"
        assert len(cmod.keys()) == key_count
        
        assert cmod.delete_value('doesntexist') is cmod, "deleting non-existing values doesn't matter"
        
        # change existing value through nested key
        key = 'section.int'
        n_val = 10
        assert cmod.value(key, n_val) == 42, "precondition requires particular value"
        assert cmod.set_value(key, n_val).value(key, n_val * 2) == n_val, "Failed to set value with nested key"
        
        assert cmod.delete_value(key).value(key, n_val * 2) == n_val * 2, "Failed to delete value with nested key"
        
    def _assert_cm_interface_nested(self, config_modifier_type):
        """Assure we can handle nested values properly"""
        cmod = config_modifier_type(self.config_data('basic.yaml'))
        
        # set a whole new section
        new_data = dict(int = 30, 
                        subsection = dict(  string = 'hi', 
                                            new_list = [1,2]),
                        new_option = 'opt')
        
        s_name = 'section'
        assert cmod.set_value(s_name, new_data) is cmod, "Expected to have cmod returned"
        # querying the value will merge the default in - lets use a nonesense default then so we get just
        # the value we set
        assert cmod.value(s_name, dict()) == new_data, "Should have set new_data in its entirety"
        assert cmod.delete_value(s_name).value(s_name, 'nonsense') is 'nonsense', "Failed to remove a nested value"
        
        # SET DATA
        ##########
        # Simple test, add all changed values
        assert cmod._data() == OrderedDict(), "expected empty data"
        cmod.set_value(s_name, new_data)    # initialize exactly one value
        assert cmod._set_data(OrderedDict()) is cmod, "Expected instance to be returned"
        assert cmod._data() != { s_name : new_data }, "Expected all our changes to be lost"
        
        
        # if there are on changes, we don't change a thing
        data = self.config_data('basic.yaml')
        cmod = config_modifier_type(data)
        
        assert cmod._set_data(OrderedDict())._data() == OrderedDict(), "The base value should have been exchanged"
        # set a new base with plenty of information
        assert cmod._set_data(data)._data() == data, "Expected non-empty configuration which equals fixture"
        
        
        # See if it only adds changed values ! Just change a single and single nested value
        key = 'section.int'
        int_val = 50
        # modification
        assert cmod.set_value(key, int_val).value(key, 20) == int_val, "Should have set the value properly"
        # deletion
        key = 'section.subsection'
        subsection = cmod.value(key, dict())
        cmod.delete_value(key)
        # addition
        assert cmod.set_value('new_section', subsection).value('new_section', dict()) == subsection
        
        # if we swap the base with a similar one, the resulting value should be exactly the same
        previous_data = deepcopy(cmod._data())
        assert cmod._set_data(data)._data() == previous_data, "Should have exactly the same state after the merge"
        
    def test_simple_values(self):
        """Verify value retrieval works with simple, non-nested values"""
        self._assert_cp_interface_simple(LooseKeyValueStoreProvider)
        
    def test_nested_values(self):
        """Assure that nested values are filled-in with defaults correctly"""
        self._assert_cp_interface_nested(LooseKeyValueStoreProvider)
        
    def test_config_modifier(self):
        """Assure the provider part of the modifier works as expected"""
        # first, assure the config provider interface still works
        self._assert_cp_interface_simple(KeyValueStoreModifier)
        self._assert_cp_interface_nested(LooseKeyValueStoreModifier)
        
    def test_config_modifier_simple(self):
        """Verify that we can deal with simple-non-nested values"""
        self._assert_cm_interface_simple(LooseKeyValueStoreModifier)
        
    def test_config_modifier_nested(self):
        """Assure we can handle nested values properly"""
        self._assert_cm_interface_nested(LooseKeyValueStoreModifier)
        
    def test_diff(self):
        log = logging.getLogger("bkvstore")
        existing_value = None
        new_value      = OrderedDict([('project_root', OrderedDict([('fs_path', '/mnt/projects')])),
                                      ('python_libs', '/foo/bar')])

        delegate = KeyValueStoreModifierDiffDelegate('', log) 

        TwoWayDiff().diff(delegate, existing_value, new_value)
        
        assert(delegate.result() == new_value)

    def test_merge(self):
        """Verify that merging one kvstore ontop of another works"""
        dict1 = {'11': 
                    {'21': 
                        {'31': 'bar', 
                         '32': {'51': 'baz'}
                         }, 
                     '22': {'41': 'blah'},
                     '23': 'foo'
                    }
                 }
        dict2 = {'11': 
                    {'21': 
                        {'32': {'51': 'Blah'} }, 
                    '23': 'Blub'}, 
                   '12': 'Blib'
                 }
        
        delegate = AdditiveMergeDelegate()
        TwoWayDiff().diff(delegate, dict1, dict2)
        
        kvstore1 = LooseKeyValueStoreModifier(delegate.result())
        assert(kvstore1.value('12',dict()) == 'Blib')
        assert(kvstore1.value('11.21.31',dict()) == 'bar')
        assert(kvstore1.value('11.21.32.51',dict()) == 'Blah')
        
        # Addition of an empty dict is okay as well
        delegate.reset()
        TwoWayDiff().diff(delegate, dict1, dict())
        assert delegate.result() == dict1, 'addition of empty dict should have resulted in just the lhs dict'
        
        # and the other way around
        delegate.reset()
        TwoWayDiff().diff(delegate, dict(), dict1)
        assert delegate.result() == dict1, 'addition of full dict onto empty one is full dict' 

    def test_defaults(self):
        schema = KeyValueStoreSchema('site', {  'name' :  str,   # can be type
                                                'location' : str(),
                                                'basename_resolver' : str(),
                                                'version_resolver' : str(),
                                                'name_recursive' : str(),
                                                'version_autoresolve' : int(),
                                                'unset_path' : Path,
                                                'empty_path' : Path,
                                                'nested' :
                                                    { 'unset_path' : Path },
                                                'root_path' : { 'repository' : 'default',
                                                                'base' : str,
                                                                'unresolvable' : '',
                                                                'software' : str,
                                                                'listed' : StringList,
                                                                'needs_list' : PathList,
                                                                'paths' : PathList,
                                                                'executable' : KVPath
                                                               },
                                                'floats' : FloatList,
                                                'ints' : IntList
                                            }
                            )
        
        # Setup (global) mapping to auto-convert versions to Version objects
        KVStringFormatter.set_key_type('version', Version)

        root = 'base'
        site_name_unresolved = 'bapp-{site.location}'
        unresolved = '{site.root_path.base}/some/viable/value'
        unresolvable = '{foo.bar}/hi'
        data = OrderedDict({ 'site' : OrderedDict({ 'name' :  site_name_unresolved,
                                        'location' : 'munich',
                                        'basename_resolver' : '{site.root_path.executable.as_KVPath.abspath.basename}',
                                        'version_resolver' : '{site.version.as_Version[0]},{site.version.as_Version.minor},{site.version.as_Version.patch}',
                                        'name_recursive' : '{site.name}',
                                        # This value is not in the schema, but can be referenced anyway.
                                        # It's a key-feature
                                        'version_autoresolve' : '{site.version.major}',
                                        'version' : '2.5.6',
                                        'empty_path' : '',
                                        'root_path' : 
                                            OrderedDict({ 'repository' : None,
                                                        'base' : root,
                                                        'unresolvable' : unresolvable, 
                                                        'software' : unresolved,
                                                        'listed' : [unresolved, unresolved, [unresolved, 5]],
                                                        'needs_list' : 'iterable',
                                                        'paths' : ['p1', '{site.root_path.paths[0]}'],
                                                        'executable' : 'foo'}),
                                        'floats' : ['1.5', '5.5', ['1.25']],
                                        'ints' : ['15', '5.5', ['1']],
                                       })
                })
                
        kvstore = KeyValueStoreProvider(data)
        value = kvstore.value(schema.key(), schema)
        
        assert value.name == site_name_unresolved
        assert value.location == 'munich'
        assert value.root_path.repository == 'default'
        assert value.root_path.base == root
        assert value.root_path.software == unresolved
        assert value.floats == [1.5, 5.5, [1.25]]
        assert value.ints == [15, 0, [1]] # last one failed as float-string doesn't convert to int
        assert len(value.root_path.listed) == 3
        assert value.root_path.needs_list == ['iterable']
        assert isinstance(value.root_path.needs_list[0], Path)
        assert len(value.root_path.paths) == 2
        assert isinstance(value.root_path.paths[0], Path)
        assert isinstance(value.root_path.paths[1], Path)
        assert isinstance(value.unset_path, Path), "unset values must be provided as desired type"
        assert isinstance(value.empty_path, Path), "null or empty values must be converted"
        assert isinstance(value.nested.unset_path, Path), 'unset nested values must end up in the desired type'
        
        # simple resolution
        resolved_path = value.root_path.software.format(**data)
        assert resolved_path.startswith(root)
        
        resolved_value = kvstore.value(schema.key(), schema, resolve=True)
        assert resolved_value.name_recursive == 'bapp-munich'
        assert resolved_value.basename_resolver == 'foo'
        assert resolved_value.version_resolver == '2,5,6'
        assert resolved_value.version_autoresolve == 2
        assert resolved_value.root_path.software == resolved_path
        assert resolved_value.root_path.unresolvable == '', 'unresolvable values are not resolved ... for now'
        assert resolved_value.root_path.listed == [resolved_path, resolved_path, [resolved_path, '5']]
        assert isinstance(resolved_value.root_path.needs_list[0], Path)
        paths = resolved_value.root_path.paths
        assert isinstance(paths[0], Path) and isinstance(paths[1], Path)
        assert paths[1] == paths[0], 'substitution should have happened'

        
    def test_globkey(self):
        """validate a variable keys data-structure"""
        schema = KeyValueStoreSchema('root', 
                                        { AnyKey :  { 
                                                        'one' : str, 
                                                        'two' : 'default', 
                                                        'three' : 3,
                                                        'multi' : { AnyKey : int },
                                                    }
                                        })
        
        data = OrderedDict({'root' : OrderedDict({
                                'good' : OrderedDict({
                                        'one' : 'g-one', 
                                        'two' : 'this', 
                                        'three' : 4,
                                        'multi' : OrderedDict({'foo' : 1, 'bar' : 2})}),
                                'worse' : OrderedDict({
                                        'one' : 5, 
                                        'two' : None, 
                                        'three' : '5', 
                                        'five' : 42}),
                            })
        })
        
        kvstore = KeyValueStoreProvider(data)
        value = kvstore.value(schema.key(), schema)
        
        assert value.good.one == 'g-one'
        assert value.good.two == 'this'
        assert value.good.three == 4
        assert sorted(value.good.multi.keys()) == ['bar', 'foo']
        assert value.good.multi.foo == 1
        assert value.good.multi.bar == 2
        
        assert value.worse.one == '5'
        assert value.worse.two == 'default'
        assert value.worse.three == 5
        assert not hasattr(value.worse, 'five'), 'five was not in schema, so it shouldnt be there'
        assert len(value.worse.multi.keys()) == 0

    def test_kvpath(self):
        """Assure properties turn out as expected"""
        path = KVPath()
        assert isinstance(path.abspath.dirname, KVPath)

# end class TestKeyValueStoreProvider
