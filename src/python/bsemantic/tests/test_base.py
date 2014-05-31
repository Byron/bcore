#-*-coding:utf-8-*-
"""
@package bsemantic.tests.test_base
@brief tests for bsemantic.base

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from minifuture import str
__all__ = []

# W0614 unused wildcard import - its okay here
# pylint: disable-msg=W0614

# test from x import *
from bsemantic import * 
from bsemantic.tests.base import Test

# ==============================================================================
## @name Utility Types
# ------------------------------------------------------------------------------
## @{

## [verified_element_node]

class VerifiedElementNode(ValidatedElementNode):
    """Tests a verified element node"""
    __slots__ = ()
    
    _schema_ =  (
                    ('format', str),        # a member 'format' which should be a string
                    ('some_val', [42]),     # a member 'some_val' which defaults to a list instance 
                )


# end class VerifiedElementNode

## [verified_element_node]

## -- End Utility Types -- @}


class TestSemantic(Test):
    __slots__ = ( )
    
    def test_element_node(self):
        """Verify the element node, as basic primitive, is working properly"""
        rules = self.path_rule_data
        assert len(rules) == 5, "Expected just one key, which is the root, and a few keys used as reference"
        
        root_key = 'root'
        root = ElementNode(root_key, root_key, rules[root_key])
        assert root.name() == root_key
        assert root.key() == root_key
        assert isinstance(root.type(), tuple)
        assert len(root.type()) == 1 
        assert root.type()[0] == 'Root'
        
        # index validate
        index = dict()
        assert root.validate(index) is root
        assert len(index) == 0, "root should be valid"
        
        assert len(root.data()) > 0
        
        # there should be children
        children = root.children()
        assert len(children) == 1, "Expected just the 'project' child'"
        assert not root.is_leaf()
        
        project = children[0]
        assert isinstance(project, ElementNode)
        assert project.key_separator in project.key()
        assert project.key_separator not in project.name()
        
        # test project's children
        children = project.children()
        assert len(children) > 10
        
        pctrl = [node for node in children if node.name() == 'ProjectControl']
        assert len(pctrl) == 1, "Expected project control node, got '%s'" % pctrl[0].name()
        pctrl = pctrl[0]
        
        # project control has default children, which are used a list
        children = pctrl.children()
        assert len(children) == 10, "Should have exactly 10 nodes, got %i" % len(children)
        
        # these are empty nodes, they have no meta-data, only a name
        for child in children:
            assert len(child.type()) == 0
            assert len(child.data()) == 0
            assert child.is_leaf()
        #end for each child
        
        # per instance parent separator override
        child_a = children[0]
        child_b = children[1]
        assert child_a.child_separator == child_b.child_separator
        child_a.child_separator = '_'
        assert child_a.child_separator != child_b.child_separator
        
    def test_validated_node(self):
        """assert the ValidatedElementNode"""
        ## [verified_element_node_usage]
        velm = ElementNodeTree.new('root', self.path_rule_data, element_node_type=VerifiedElementNode).root_node()
        
        assert velm.format == "{project.root_path.fs_absolute}"  # this is the value from the data
        assert velm.some_val == [42]        # this value defaulted
        self.failUnlessRaises(AttributeError, getattr, velm, 'undefined')
        ## [verified_element_node_usage]
        index = dict()
        assert velm.validate(index) is velm
        assert not index
        
    def _assert_element_node_list(self, nlist):
        """verify functionality of element node list"""
        assert len(nlist) > 0, "nlist should not be empty"
        self.failUnless(nlist.is_leaf() == (len(nlist[-1].children()) == 0))
        
        assert nlist.find_first_if(lambda elm: 'Root' in elm.type()), "Every node list should have a type"
        assert not str(nlist).startswith(nlist[-1].child_separator)
        
        # just make the call to execute code - it can complain about a few things that subclasses may implement
        # differently
        index = dict()
        for elm in nlist:
            elm.validate(index)
        #end for each element
        
    def test_tree_iterator(self):
        """Verifies the tree iterator works"""
        ntree = ElementNodeTree.new('root', self.path_rule_data, ElementNode)
        node_lists = list(ntree)
        assert len(node_lists) > 1, "Got only %i node_lists, expected many more" % len(node_lists)
        assert isinstance(ntree.root_node(), ElementNode)
        
        assert len(list(ntree.iterate(predicate=lambda node: False))) == 0, "Predicate was ignored"
        assert len(list(ntree.iterate(prune=lambda node: True))) == 1, "Should only get root node on prune-all"
        
        names = set()
        for nlist in node_lists:
            self._assert_element_node_list(nlist)
            names.add(str(nlist))
        #end for each element list
        assert len(names) == len(node_lists), "Expected unique node names"
        
        # try validation
        index = dict()
        ntree.validate(index)
        
        # it will find unset types, defaults should be handled by subtypes
        assert len(index)
        

# end class TestSemantic
