#-*-coding:utf-8-*-
"""
@package bsemantic.tests.test_generators
@brief tests for bsemantic.generators

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str
__all__ = []

# W0614 unused wildcard import - its okay here
# pylint: disable-msg=W0614

# test from x import *
from bsemantic import ElementNodeTree
from bsemantic.generators import *
from bsemantic.tests.base import Test
from butility import DictObject


class TestGenerators(Test):
    __slots__ = ()

    def test_formatting(self):
        """Test basic node formatting"""
        tree = ElementNodeTree.new('root', self.path_rule_data, element_node_type=StringFormatNode)
        root = tree.root_node()
        assert isinstance(root, StringFormatNode)

        assert isinstance(root.format_string(), str)
        assert len(root.format_keys()) == 1
        assert root.format_keys()[0].count('.') == 2

        assert len(root.format_data()) == 0

        assert root.format_result is None, "default result should be None"
        assert not root.format_data()
        assert root.apply_format(dict()).format_result is None, "Should have no result if substitution failed"
        assert not root.format_data()

        data = dict(project='something')
        assert root.apply_format(data).format_result is None, "It should not throw if it cannot resolve the key"
        data = self.base_data()
        assert root.apply_format(DictObject(data)).format_result == self.fs_root
        fmt_data = root.format_data()
        assert len(fmt_data) == 1 and isinstance(fmt_data['project'], dict)  # check nesting

        # if we assign with some incomplete dict once again, the result is reset
        assert root.apply_format(dict()).format_result is None
        assert not root.format_data()

        # it is possible to reformat the node with the returned data
        assert root.apply_format(DictObject(fmt_data)).format_result is not None
        assert root.format_data() == fmt_data

        # TREE ITERATION
        ################
        string_tree = StringFormatNodeTree.new('root', self.path_rule_data)
        assert len(list(string_tree)) == len(
            list(tree)), "default iteration should be the same for both implementations"
        assert len(list(string_tree.iterate_formatted_nodes(dict()))) == 0, "Without any data, nothing is returned"

        snode_lists = list(string_tree.iterate_formatted_nodes(data))
        assert len(snode_lists) == 1, "Got more/less than the eixpected single list: %s" % str(snode_lists)
        node_list = snode_lists[0]
        assert len(node_list) == 1, "Should have only one node"
        assert node_list[0] is string_tree.root_node(), "the only contained string node should be the root"

        # assert concatenation with different separators works. Note that we work on node-references here
        new_sep = '#'
        assert new_sep not in node_list.to_string()
        node_list.extend(node_list)
        # this affects one and the same root, the first node in a list will not contribute its parent separator
        node_list[-1].child_separator = '#'
        assert node_list.to_string().count(new_sep) == 1

        assert len(list(string_tree.iterate(predicate=lambda nlist: False))) == 0, "iterate ignored the predicate"

        # add more data to get more paths
        data['project'].code = 'my_project'
        snode_lists = list(string_tree.iterate_formatted_nodes(data, prune=lambda nlist: len(nlist) > 2))
        assert len(snode_lists) == 1, "expected one longer node lists, got %i" % len(snode_lists)
        assert len(snode_lists[0]) == 2, "Should have two nodes in it"

        snode_lists = list(string_tree.iterate_formatted_nodes(data, predicate=lambda nlist: False))
        assert len(snode_lists) == 0, "predicate has no effect"

        # without the prune method, many more would be valid, as we have many nodes that don't need any data
        snode_lists = list(string_tree.iterate_formatted_nodes(data))
        assert len(snode_lists) > 15, "should have many more lists"

        # STRING NODE LISTS ASSERTIONS
        ##############################
        names = set()
        for nlist in snode_lists:
            nlist_string = nlist.to_string()
            names.add(nlist_string)

            # should have the same result, as the data is exactly the same
            assert nlist.apply_format(data).to_string() == nlist_string

            # also we assume that we don't get short lists, as we return the longest ones only
            assert len(nlist) > 2, "Expected long lists, got one of length %i" % len(nlist)
        # end for each nlist
        assert len(names) == len(snode_lists), "expected unique path names"

# end class TestGenerators
