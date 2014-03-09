#-*-coding:utf-8-*-
"""
@package tx.tests.template.test_inference
@brief tests for tx.template.inference

@copyright 2012 Sebastian Thiel
"""
__all__ = []

# test from x import *
from bcore.template import (
                                StringFormatNode,
                                StringFormatNodeTree
                              )
from bcore.template.inference import *
from bcore.tests.template.base import TestTemplateBase
from bcore.utility import DictObject
from bcore.core.kvstore import (
                                KeyValueStoreProvider,
                                ValidatedKeyValueStoreSchema, 
                                KeyValueStoreSchemaValidator
                            )


class TestInference(TestTemplateBase):
    __slots__ = ()
    
    @classmethod
    def base_data(cls):
        """@return a richer version of the base data we usually have"""
        data = super(TestInference, cls).base_data()
        data.project.code = 'my_project'
        return data
        
    def complete_data(self):
        """prepare a full data set and return it"""
        data = self.base_data()
        data.asset = DictObject(dict(code='bicycle'))
        data.workflow = DictObject(dict(name='modeling', code='mdl', step='layout'))
        data.resource = DictObject(dict(variation='dirty', version=15, ext='ma'))
        data.texture = DictObject(dict(type='color', name='torso', ext='tif'))
        data.user = DictObject(dict(code='thielse'))
        return data
        
        
    def test_inference(self):
        """test basic functionality"""
        stree = StringFormatNodeTree.new('root', self.path_rule_data)
        data = self.base_data()
        
        root_path = stree.root_node().apply_format(data).format_result
        # start simple, just back-substitute the root
        itree = InferenceStringFormatNodeTree.new('root', self.path_rule_data)
        
        # NO DATASET, ORIGINAL PATH
        ############################
        # without a data-delgate, we shouldn't be able to find the correct root, but should get a match 
        # anyway as we substitute root/project, which is similar to /mnt/projects
        delegate = InferenceStringFormatNodeTreeDelegate()
        matches = list(itree.iterate_matches(root_path, delegate=delegate))
        assert len(matches) == 0, "Should have exactly no match"
        
        
        # NO DATASET, TRUNCATED PATH
        ############################
        # if we don't have the leading slash (which is somewhat special to the system), we have matches
        # as it will match the first two nodes as individual parts of the path
        assert root_path.startswith(StringFormatNode.default_child_separator)
        truncated_root_path = root_path[len(StringFormatNode.default_child_separator):]
        
        matches = list(itree.iterate_matches(truncated_root_path, delegate=delegate))
        assert len(matches) == 1
        assert len(matches[0]) == 2, "should have found root and project node"
        
        # obviously, these values are wrong, but its expected in this case as we didn't provide substitution data
        tokens = self.fs_root.split('/')
        assert len(tokens) == 3 # first index is empty string
        pdata = delegate.parsed_data()['project']
        assert pdata['root_path']['fs_absolute'] == tokens[1]
        assert pdata['code'] == tokens[2]
        
        # additionally, add some made-up piece that will result in a partial match only
        appendix = StringFormatNode.default_child_separator + data.project.code
        truncated_root_path += appendix
        matches = list(itree.iterate_matches(truncated_root_path, delegate=delegate))
        assert len(matches) == 0, "shouldn't have a full match anymore"
        partial_matches = list(itree.iterate_partial_matches(truncated_root_path, delegate=delegate))
        
        assert len(partial_matches) == 1, "Should have one partial match"
        assert partial_matches[0][0] == data.project.code, "The unconsumed portion was unexpected"
        
        
        # SINGLE DATASET, ORIGINAL PATH
        ###############################
        # try resolution with a single dataset
        delegate = InferenceStringFormatNodeTreeDelegate([data])
        # make sure we can also handle the project (yes, we should get this path from the stree iterator, but
        # this path is quite stable in our case, so I take the risk)
        root_path = root_path + appendix
        matches = list(itree.iterate_matches(root_path, delegate=delegate))
        
        assert len(matches) == 1, "Should have exactly one list"
        assert len(matches[0]) == 2, "Should have found two nodes"
        
        pdata = delegate.parsed_data()
        assert len(pdata) == 1, "expected just the 'project' key, found %i keys" % len(pdata)
        pdata = pdata['project']
        assert len(pdata) == 2, "expected the root path and project code only"
        assert len(pdata['root_path']) == 1, "expected fs_root' only"
        assert pdata['root_path']['fs_absolute'] == self.fs_root
        assert pdata['code'] == data.project.code
        
        # predicate and prune
        assert len(list(itree.iterate_matches(root_path, delegate=delegate, predicate=lambda nlist: False))) == 0
        # we get the root only
        assert len(list(itree.iterate_matches(root_path, delegate=delegate, prune=lambda nlist: False))) == 1
        
    def test_mass_inference(self):
        """generate many more paths and infer them right away"""
        stree = StringFormatNodeTree.new('root', self.path_rule_data)
        itree = InferenceStringFormatNodeTree.new('root', self.path_rule_data)
        
        # the delegate only has information about the root path and the project name, 
        # everything else will be inferred
        delegate = InferenceStringFormatNodeTreeDelegate([self.base_data().clone()])
        
        # MASS TEST
        ###########
        # In this test we only have two substitutions, the projects root and the code. All other formats
        # are just names, which should be resolved as well.
        # Make sure we can substitute as many paths as possible, thus we add some more information
        count = 0
        data = self.complete_data()
        
        assert 'asset' not in delegate.parsed_data(), "precondition failed"
        # we need this predicate, as we may have ambiguity in the tree (at least with our limited dataset)
        predicate = InferenceStringFormatNodeTree.leaf_nodes_only
        for nlist in stree.iterate_formatted_nodes(data):
            count += 1
            matches = list(itree.iterate_matches(nlist.to_string(), delegate=delegate, predicate=predicate))
            assert len(matches) == 1, "should have exactly one full match from a previously generated path"
        #end for each nodelist
        assert count, "should have processed quite some paths"
        
        # quick diff - there should be no differences (which are not overcome by converting from one type to another)
        validator = KeyValueStoreSchemaValidator()
        for key, value in data.iteritems():
            ValidatedKeyValueStoreSchema(key, value, validator = validator)
        #end for each key, value
        assert type(delegate.parsed_data()['resource']['version']) is int
        assert len(validator) and len(validator.validate_provider(KeyValueStoreProvider(delegate.parsed_data()))) == 0
        
    def test_extension(self):
        """Show how to extend the system
        @todo set the version and have an easy way to reformat the node list with the changes"""
        ## [name-handling-extension]
        class DynamicNode(StringFormatNode):
            """A node dynamically returning types based on the data type"""
            def _child_type(self, child_key, data):
                """Extract the child's type and return the actual type to use for the child"""
                if isinstance(data, dict):
                    meta = data.get(self.attr_metadata)
                    if meta:
                        types = meta.get(self.attr_type, dict())
                        if 'Version' in types:
                            return VersionNode
                        #end handle version
                    #end have meta data
                #end have a dict input
                return super(DynamicNode, self)._child_type(child_key, data)
        # end class DynamicNode
        
        class VersionNode(DynamicNode):
            """A version node """
            _schema_ = (('version', 0),)
            
            def _obtain_meta_data_for(self, key):
                """@return meta data either from the parsed source, or from meta data"""
                if key in self.format_data():
                    return self.format_data()
                return super(VersionNode, self)._obtain_meta_data_for(key)
            
            # -------------------------
            ## @name Interface
            # @{
            
            def set_version(self, version):
                """Set our version to the given value
                @note this is just the type-checked variant of self.version, which is supported due to our
                ValidatedElementNodeBase heritage"""
                if not isinstance(version, int):
                    raise ValueError("invalid value type")
                self.version = version
            ## -- End Interface -- @}
        # end class VersionNode
        
        
        stree = StringFormatNodeTree.new('root', self.rule_data('simple_version.yaml'), element_node_type=DynamicNode)
        assert isinstance(stree.root_node(), StringFormatNode)
        is_version_node = lambda node: type(node) is VersionNode
        count = 0
        stree.root_node().children()
        version = 15
        data = dict(version = version)
        # substitute the simple version data in
        iterator = stree.iterate_formatted_nodes(data, predicate=lambda nlist: nlist.find_first_if(is_version_node))
        for node_list in iterator:
            count += 1
            version_node = node_list.find_first_if(is_version_node)
            
            assert version_node.version == version
            version_string = version_node.format_result
            
            # Currently we have to do it manually
            version_data = version_node.format_data()
            version_data['version'] = version + 1
            
            assert version_string != version_node.apply_format(DictObject(version_data)).format_result
        #end for each node-list
        assert count
        
        ## [name-handling-extension]
            
        
        
        
        

# end class TestInference
