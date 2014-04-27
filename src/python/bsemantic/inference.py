#-*-coding:utf-8-*-
"""
@package from bsemantic.inference
@brief Module with implementations for ElementNodeList inference.

These algrithms allow to infer the NodeList and its data used to create a previously generated name, based on
sample ruleset.

@copyright 2012 Sebastian Thiel
"""
__all__ = ['InferenceStringFormatNodeTreeDelegate', 'InferenceStringFormatNodeTree']

import logging


from . import parse

from .generators import StringFormatNodeTree
from bkvstore import UnorderedKeyValueStoreModifier
                                


class InferenceStringFormatNodeTreeDelegate(object):
    """A simple abstract interface which defines a protocol to allow the InferenceStringFormatNodeTree to work."""
    __slots__ = (
                    '_data_sets',       # a list or tuple of data for substituting nodes, may be empty
                    '_parsed_data',     # a dictionary of DictObjects with the parsed (nested) data
                )
    
    log = logging.getLogger('bsemantic.inference')
    
    
    def __init__(self, data_sets=list()):
        """Initialze this instance with an optional list of data sets
        @param data_sets a list or tuple of data sets suitable to be fed to the `apply_format()` method of 
        `StringFormatNode` instances"""
        self._data_sets = data_sets
        self._parsed_data = dict()
        
    def _try_parse_data(self, node, piece):
        """Using the format in the given node, try to parse the given piece and re-acquire the data that created it
        originally.
        @return True on parse-success, False on failure.
        @param node a `StringFormatNode` compatible node
        @param piece a string which was previously returned by `iterate_consumption_candidates`
        """
        try:
            result = parse.parse(node.format_string(), piece, re_flags=0)
            if result is None:
                return False
            if result.fixed:
                raise ValueError("Format shouldn't have fixed arguments")
            #end make assertion
        except ValueError:
            self.log.error("Ignored format as it could not be parsed: '%s'" % node.format_string(), exc_info=True)
            return False
        #end handle exceptions
        
        # put keys into our data - its okay to have no keys, not all formats have them
        if result.named:
            kvstore = UnorderedKeyValueStoreModifier(self._parsed_data)
            for nested_key, value in result.named.iteritems():
                kvstore.set_value(nested_key, value)
            #end for each key to store
            # kvstore copies the data, therefore we have to get it back - its somewhat inefficient, but good
            # enough for now. Could use the private API, _data(), to get a reference, but lets not go there.
            self._parsed_data = kvstore.data()
        #end fill data dict by keys
        return True
        
    # -------------------------
    ## @name Interface
    # @{
    
    def consume_string(self, node_list, string):
        """@return the piece (starting at the left most character of the `string`) which we could consume
        using information in the given node, or an empty string/None if there was no match.
        @param node_list a `StringFormatNodeList` compatible instance which is currently being tested. The last
        node in it is the one which should make the substitution.
        @param string the (remainder) of the string to be consumed. The parent's separator will have been stripped
        from it already, if this is not the very first level, as we don't assume to have a parent separator"""
        node = node_list[-1]
        # first, substitute our data sets and attempt to match the result with the beginning of the string.
        # For this we jsut try the biggest possible string which could be our own data-set substitution. 
        node_format_data = node.format_data()
        for data in self._data_sets:
            node.apply_format(data)
            piece = node.format_result
            # restore previous format right away
            node.apply_format(node_format_data)
            
            if piece is not None and string.startswith(piece):
                if self._try_parse_data(node, piece):
                    # if the next item after the piece is our separator, consume it as well
                    if len(piece) < len(string) and string[len(piece)] == node.child_separator:
                        piece += node.child_separator
                    #end consume child separator too
                    return piece
                # no need for break
            #end check if piece matches
        #end for each data
        
        # the caller will assume there is no separator at the beginning of the name, as there is no
        # respective parent node that would provide this information.
        # If this is the case, we must handle the case that we could not back-substitute it (above)
        # and have a leading token
        index = -1
        if node.child_separator in string:
            index = string.index(node.child_separator)
        #end obtain useful separator index
        if index > -1:
            if index == 0:
                # abort, we never try to substitute 'invalid' strings, the parent separator should not be here
                # (and we should have managed to resolve it in the step above)
                # NOTE: This happens for instance if the name starts with a separator, which it shouldn't
                # unless the first part was substituted and the substitution included the parent separator.
                # We deal with it gracefully
                return None
            else:
                piece_with_sep = string[:index+1]       # piece with separator
                piece = string[:index]                  # piece without separator
            # end if there is an index
        else:
            # its just the last element of the string
            piece = piece_with_sep = string
        #end handle index
        
        # return the complete matching piece including separator, as can't be handled by our child nodes
        if self._try_parse_data(node, piece):
            return piece_with_sep
        #end parse piece again
        return None
        
    def parsed_data(self):
        """@return a nested dictionary which associates the (nested) data keys found in the nodes formats with
        the value obtained from the parsed string
        """
        return self._parsed_data
    
    ## -- End Interface -- @}
    

# end class InferenceStringFormatNodeTreeDelegate

# Each generator node should come with a version that is able to infer the functionality of its respective 
# generator. This allows them to re-retrieve the information the generator used to generate a given string.

# There are different algorithms using a node tree in order to disect a given string. This results in 0 or more
# matching node lists from which the information can be read.

class InferenceStringFormatNodeTree(StringFormatNodeTree):
    """Implements a search algorithm which tries to find matching NodeLists from a string.
    
    A delegate compatible to the InferenceStringFormatNodeTreeDelegate is used to encapsulate additional details
    that this base implementation cannot deal with itself.
    
    The implementation allows you to efficiently search for node lists obtained from an existing ElementNode's
    hierarchy which are able to produce a given string or part thereof. The search is always top-down, that is
    from the left to the right of the string.
    
    If there is no full match, no node list will be returned.
    
    The obtained node lists, if formatted, will yield the string that was supposed to be found. Additionally
    they will have obtained all data that was required to do so.
    
    How it Works
    ============
    
    Lets have a look at a simple example:
    Given are a string "a/b/c" and an element tree `a`->`b`, where `a` is the parent of `b`. The string was 
    originally generated by some node list from our rule set, and the goal is to infer that nodelist and its
    values from the string.
    
    The algorithm will try to consume the string left to right, while walking the node tree from the root
    breadth-first to all children, if the parent of the respective child matched as well.
    
    The matchings intention is to consume as much as possible at once. There are two modes. 
    First we try to match the left part of the string with the formatted value of the current node, 
    which may match any portion of the string, independently of the separators.
    
    If there is no formatted value, or no match for it, the left-most element of the string will be extracted
    in the attempt to infer substitution values based on the current node's format. If that succeeds, we have a
    match and may proceed to the children of the node, as long as there is an unconsumed part of the string.
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    DefaultDelegateType = InferenceStringFormatNodeTreeDelegate 
    
    ## -- End Configuration -- @}
    
    # R0913 too many arguments - I really need those though
    # pylint: disable-msg=R0913
    def _iterate_partial_matches_at(self, node_list, string, delegate, predicate=None, prune=None, _child_info=None):
        """Implements the partial matching algorithm using the given delegate
        @note the returned node lists will be one and the same, we do not clone it for performance reasons.
        Thus you must do this before returning the desired results to the user
        """
        # abort if we have consumed the string
        if not string:
            raise StopIteration()
        #end check for string consumtion
        node = node_list[-1]
        
        # attempt to perform the substitution
        consumed_piece = delegate.consume_string(node_list, string)
        if consumed_piece:
            assert string.startswith(consumed_piece), "delegate should have taken a piece off the beginning"
            string = string[len(consumed_piece):]
            # let parent know that we succeeded
            if _child_info:
                _child_info[0] |= True
            #end update child info
        else:
            # abort if there was nothing
            raise StopIteration
        #end cut string
        
        # still here - call all children, and return only the longest path, i.e. if there was no child
        # which had a valid path
        # don't even try without anything to substitute
        has_valid_child = [False]
        if string and (prune is None or not prune(node_list)):
            for child in node.children():
                node_list.append(child)
                try:
                    for result in self._iterate_partial_matches_at(node_list, string, delegate,
                                                                                _child_info=has_valid_child,
                                                                                predicate=predicate, prune=prune):
                        yield result
                    #end for each result to yield
                finally:
                    node_list.pop()
                #end assure nodelist consistency
            #end for each child
        #end if there is some string to consume
        
        if not has_valid_child[0]:
            if predicate is None or predicate(node_list):
                yield string, node_list
        #end check if yield is possible
        
    # -------------------------
    ## @name Predicates
    # Contains default predicate implementations that are generic and useful
    # @{
    
    @classmethod
    def leaf_nodes_only(cls, node_list):
        """@return True only if the last node list is a leaf. This assures we have the most specific match"""
        return node_list.is_leaf()
        
    
    ## -- End Predicates -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def iterate_matches(self, string, delegate=None, predicate=None, prune=None):
        """@return an iterator to yield all full matches as `StringFormatNodeList` instances
        @param string the string to find matching node lists for
        @param delegate an `InferenceStringFormatNodeTreeDelegate` compatible instance. If None, a default 
        instance will be created. The reason you may wish to have your own is if you suspect the necessity
        for testing the string against multiple datasets that could have been used for substitution.
        @param predicate a function returning True for each node list that the iterator should yield,
        signature is (bool) fun(node_list). If None, it will be ignored.
        @param prune a function returning true if the children of the given node list should be iterated, signature 
        is (bool)fun(node_list). If None, it will be ignored
        @note if you do not provide your own delegate instance, you will not be able to obtain the data 
        parsed from the StringFormatNode's format information.
        @note if ther was no match, you may want to try `iterate_partial_matches` as it will return the 
        remainder of the given string as well.
        """
        for remainder, nlist in self.iterate_partial_matches(string, delegate=delegate, 
                                                                    predicate=predicate, prune=prune):
            if not remainder:
                yield nlist     # its already cloned
            #end ignore partial matches
        #end for each (partial) match
        
    def iterate_partial_matches(self, string, delegate=None, predicate=None, prune=None):
        """@return an iterator to yield all partial matches as tuple of the unmatched portion of the string
        and the corresponding node list which matched the string.
        Please note that you will not see nodes that didn't match at all. The remainder/unmatched portion
        may be an empty string, which makes the corresponding node list a full match
        @param string see `iterate_matches`
        @param delegate see `iterate_matches`
        @param predicate see `iterate_matches`
        @param prune see `iterate_matches`
        """
        nlist_base = self.ElementNodeListType()
        nlist_base.append(self.root_node())
        
        for remainder, nlist in self._iterate_partial_matches_at(nlist_base, string, 
                                                                    delegate or self.DefaultDelegateType(),
                                                                    predicate=predicate,
                                                                    prune=prune):
            yield (remainder, nlist.clone())
        #end for each nlist
    
    ## -- End Interface -- @}

# end class InferenceStringFormatNodeTree

