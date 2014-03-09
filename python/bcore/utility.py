#-*-coding:utf-8-*-
"""
@package tx.utility

Practical and useful functions which are not dependent on other parts of the tx
library

@copyright 2012 Sebastian Thiel
"""
__all__ = [ 'login_name', 'uname', 'int_bits', 'wraps', 'LazyMixin', 'OrderedDict', 'NonInstantiatable', 
            'is_mutable', 'smart_deepcopy', 'DictObject', 'dylib_extension', 'system_user_id', 'GraphIteratorBase',
            'Version', 'update_env_path', 'Singleton', 'init_ipython_terminal', 'capitalize', 'StringChunker',
            'ConcurrentRun', 'ProgressIndicator']

from UserDict import DictMixin  # for OrderedDict
import platform
import getpass
import functools
import os
import re
import sys
import pprint

import threading
from collections import deque

from copy import deepcopy

from .path import Path

import bcore.base


# REVIEW: merge into Environment class
# ==============================================================================
## @name System Related Functions
# ------------------------------------------------------------------------------
# They are platform-independent !
## @{

def init_ipython_terminal():
    """Setup ipython for use in a terminal"""
    import IPython
    if hasattr(IPython, 'Shell'):
        ips = IPython.Shell.IPShell(argv=sys.argv[:1])
        ips.mainloop()
    else:
        import IPython.frontend.terminal.interactiveshell
        IPython.frontend.terminal.interactiveshell.TerminalInteractiveShell().mainloop()
    # end handle different API versions 


def dylib_extension():
    """@return extension used for dynamically loaded libraries on the current platform
    @throws EnvironmentError if platform is unknown"""
    try:
        return {    'linux2' : "so",
                    'darwin' : "bundle",
                    'win32'   : "dll"}[sys.platform]
    except KeyError:
        raise EnvironmentError("Unknown platform: %s" % sys.platform)
    #end convert key error to environment errror


def login_name():
    """
    Cross-platform way to get the current user login

    @attention this uses an environment variable in Windows, technically allows
    users to impersonate others quite easily.
    """
    # getuser is linux only !
    if sys.platform == 'win32':
        return os.environ['USERNAME']
    else:
        return getpass.getuser()
    #end handle platforms


def uname():
    """
    Cross-platform way to return a tuple consisting of:
    (sysname, nodename, release, version, machine), analogous to `os.uname`
    """
    try:
        pterse = platform.platform(terse=1)
    except IOError:
        # some host applications will have a directory as executable for some reason ... (katana)
        pterse = 'unknown'
    #end handle very special case
    return tuple([pterse, platform.node(),
                 platform.release(), platform.version(), platform.machine()])
    
def int_bits():
    """@return integer identifying the amount of bits used to represent an integer
    @throws EnvironmentError if the platform is neither 32 nor 64 bits
    """
    try:
        return { 9223372036854775807 : 64,
                          2147483647 : 32 }[sys.maxint]
    except KeyError:
        raise EnvironmentError("maxint size uknown: %i" % sys.maxint)
    #end convert keyerror to environmenterror
    
    
def system_user_id():
    """@return string identifying the currently active system user as name\@node
    @note user can be set with the 'USER' environment variable, usually set on windows"""
    ukn = 'UNKNOWN'
    username = os.environ.get('USER', os.environ.get('USERNAME', ukn))
    if username == ukn:
        username = login_name()
    # END get username from login
    return "%s@%s" % (username, platform.node())
    
def update_env_path(variable_name, path, append = False, environment = os.environ):
    """Set the given variable_name to the given path, but append or prepend the existing path
    to it using the platforms path separator.
    
    @param variable_name name of the environment variable to set
    @param path to append/prepend to the variable
    @param append if True, path will be appended to existing paths, otherwise it will be prepended
    @param environment the environment dict to adjust"""
    curval = environment.get(variable_name, None)
    # rule out empty strings
    if curval:
        if append:
            path = curval + os.pathsep + path
        else:
            path = path + os.pathsep + curval
        # END handle append
    # END handle existing path
    # environment can only contain strings - at least if used for subprocess, which must be assumed
    environment[variable_name] = str(path)

# -- End System Related Functions -- @}


# ==============================================================================
## @name Math
# ------------------------------------------------------------------------------
# @note maybe this should go into a separate module at some point
## @{

def equals_eps(float_left, float_right, epsilon = sys.float_info.epsilon):
    """@return True if float_left equals float_right within an error of epsilon"""
    return abs(float_left - float_right) <= epsilon
    

## -- End Math -- @}



# ==============================================================================
## \name Filesystem Utilities
# ------------------------------------------------------------------------------
## \{

def tagged_file_paths(directory, taglist, pattern=None):
    """Finds tagged files in given directories and return them.
    
    The files retrieved can be files like "file.ext" or can be files that contain tags. Tags are '.'
    separated tokens that are to be matched with the tags in taglist in order.

    All tags must match to have it returned by this function.

    Suppose you have two paths, one is a global one in a read-only location,
    another is a local one in the user's home.

    The list of file-paths (tx.path instances) returned would be all matching files from the global path and
    all matching files from the local one, sorted such that the file with the smallest amount
    of tags come first, files with more tags (more specialized ones) will come after that. 

    @param directory iterable of directory paths to look in for files, or a single directory
    @param taglist list or tuple of tags of tags, like a tag for the operating system, or the user name, e.g.
    ('win', 'project', 'maya')
    @param pattern simple fnmatch pattern as used for globs or a list of them (allowing to match several
        different patterns at once)
    @return list of matches file paths (as mrv Path)
    """
    from bcore.core.logging import module_logger
    log = module_logger('tx.utility')
    log.debug('obtaining tagged files from %s, tags = %s', directory, ', '.join(taglist))
    
    container_types = (list , set, tuple)
    # verify input
    ###############
    directory_list = directory
    if not isinstance(directory, container_types):
        directory_list = [directory]
    #end convert to type we require
    
    pattern_list = pattern
    if not isinstance(pattern, container_types):
        pattern_list = [pattern]
    # end convert pattern type


    # GET ALL FILES IN THE GIVEN DIRECTORY_LIST
    ########################################
    matched_files = list()
    for folder in directory_list:
        for pattern in pattern_list:
            matched_files.extend(Path(folder).files(pattern))
        # END for each pattern/glob 
    # end for each directory

    # APPLY THE PATTERN SEARCH
    ############################
    tag_match_list = list()
    for tagged_file in sorted(matched_files):
        filetags = os.path.split(tagged_file)[1].split('.')[1:-1]

        # match the tags - take the file if all can be found
        num_matched = 0
        for tag in taglist:
            if tag in filetags:
                num_matched += 1

        if num_matched == len(filetags):
            tag_match_list.append((num_matched, tagged_file))
    # end for each tagged file

    out_files = list()
    for _, tagged_file in sorted(tag_match_list):
        out_files.append(tagged_file)
    # end for each sorted tag
    return out_files

#} end Utilities

## -- End Filesystem Utilities -- @}



# ==============================================================================
## \name General Utilities
# ------------------------------------------------------------------------------
## \{

def is_mutable( value):
    """Recursively check if the given value is mutable.
    
    A value is considered mutable if at least one contained value is mutable
    @param value a possibly nested value of built-in types
    @return true if value is mutable"""
    if isinstance(value, (basestring, int, float, type(None))):
        return False
    #end check immutable
    if isinstance(value, (list, dict)):
        return True
    #end check mutable
    
    if isinstance(value, tuple):
        for item in value:
            if is_mutable(item):
                return True
            #end abort recursion if item is mutable
        #end for each item to check in tuple
    #end handle tuple value
    
    return False
    
def smart_deepcopy(value):
    """Create a deep copy of value only if this is necessary as its value has mutable parts.
    @return a deep copy of value if value was mutable
    @note checking for its mutability will cost additional time - its a trade-off between memory and 
    CPU cycles"""
    if is_mutable(value):
        return deepcopy(value)
    return value
    
def capitalize(self):
    """@return self with first letter capitalized"""
    return self[0].upper() + self[1:]

## -- End Subclass Utilities -- @}


# ==============================================================================
## @name Decorator Tools
# ------------------------------------------------------------------------------
# Tools useful in conjunction with decorators.
## @{

def wraps(func):
    """Wrapper around the default 'wraps' utility to opt-in on additional
    improvements or fixes"""
    return functools.wraps(func)

## -- End Decorator Tools -- @}

# ==============================================================================
## \name Mixins
# ------------------------------------------------------------------------------
# A category of classes from which you can derive to add a certain interface
# to your type. You might have to implement some protocol methods though,
# depending on the actual mixin.
## \{

# R0201 method could be a function - no, it just didn't detect that self is in fact used in _clear_cache_
# pylint: disable-msg=R0201

class LazyMixin(object):
    """Base class providing an interface to lazily retrieve attribute values upon
    first access. This is efficient as objects can be created without causing
    overhead at creation time, delaying necessary overhead to the time the
    respective attribute is actually used.
    
    If slots are used, memory will only be reserved once the attribute
    is actually accessed and retrieved the first time. All future accesses will
    return the cached value as stored in the Instance's dict or slot.
    
    Here is how you implement your subtype
    @snippet bcore/tests/doc/test_examples.py LazyMixinExample Implementation
    
    In code, you can use the lazy attributes natively, its entirely transparent
    to the caller.
    Ideally, this system is used for internal attributes which will be set on first
    use, maybe by reading from a file or a slow device.
    
    @snippet bcore/tests/doc/test_examples.py LazyMixinExample Example
    """
    __slots__ = tuple()
    
    def __getattr__(self, attr):
        """Whenever an attribute is requested that we do not know, we allow it 
        to be created and set. Next time the same attribute is requested, it is simply
        returned from our dict/slots."""
        self._set_cache_(attr)
        # will raise in case the cache was not created
        return object.__getattribute__(self, attr)

    def _set_cache_(self, attr):
        """This method should be overridden in the derived class. 
        It should check whether the attribute named by `attr` can be created
        and cached. Do nothing if you do not know the attribute or call your subclass'
        _set_cache_ method
        
        The derived class may create as many additional attributes as it deems 
        necessary."""
        pass
    
    def _clear_cache_(self, lazy_attributes):
        """Delete all of the given lazy_attributes from this instance.
        This will force the respective cache to be recreated
        @param lazy_attributes iterable of names of attributes which are to be deleted"""
        for attr in lazy_attributes:
            try:
                del(self, attr)
            except AttributeError:
                pass
            #end ignore non-existing keys
        #end for each attribute

## -- End Mixins -- \}

class NonInstantiatable(object):
    """A mixin which will makes it impossible to instantiate derived types
    
    @throws TypeError if someone tries to create an instance"""
    __slots__ = ()

    # since this prevents the instantiation of the object,
    # the arguments to new aren't used
    # pylint: disable=W0613
    def __new__(cls, *args, **kwargs):
        """Prevents instantiation"""
        raise TypeError("This type cannot be instantiated")
    # pylint: enable=W0613
# end class NonInstantiatable


class GraphIteratorBase(object):
    """A generic, none-recursive implementation of a graph-iterator, which is able to handle cycles.
    
    Its meant to be subclassed to make the interface more approachable
    @attention this approach is only useful if you don't care about the order or of your nodes are able
    to provide all the information you like right away (like information about the parent)
    @todo add a test for this type - its not even indirectly used yet. Alternatively, remove it if its not used
    by anybody"""
    __slots__ = ()
    __metaclass__ = tx.base.MetaBase
    
    # W0613 ignore the unused arguments we have here, its part of an abstract method
    # pylint: disable-msg=W0613
    # -------------------------
    ## @name Constants
    # @{
    
    upstream = 'upstream'           # a direction towards the root
    downstream = 'downstream'       # a direction towards childdren
    
    directions = [upstream, downstream]
    
    breadth_first = 'breadth_first' # visit every node in each level of a tree first
    depth_first = 'depth_first'     # traverse along each branch to each leaf node, and backtrack
    
    traversal_types = [breadth_first, depth_first]
    
    ## -- End Constants -- @}
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## if True, the root of the iteration will not be returned, otherwise it will.
    skip_root_node = False
    
    ## visit_once if True, items will only be returned once, although they might be encountered
    ## several times if there are loops for instance, or cross-overs. If you have self-loops, this is the only
    ## way to prevent endless loop.
    ## @note this costs time as a tracking set has to be kept and updated, so you should set it as required.
    ## Its enabled by default to prevent costly bugs - turn it of if you do cycle checks yourself
    visit_once = True
    
    ## max_depth define at which level the iteration should not go deeper
    ## - if -1, there is no limit
    ## - if 0, you would only get root_item
    ##   + e.g. if 1, you would only get the root_item and the first level of predessessors/successors
    max_depth = -1
    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Subclass Methods
    # These methods are to be implemented or customized by subclasses
    # @{
    
    @tx.base.abstractmethod
    def _successors(self, node):
        """@return an iterable of successor nodes (i.e. output nodes) of the given node"""
        
    @tx.base.abstractmethod
    def _predecessors(self, node):
        """@return an iterable of predecessor nodes (i.e. input nodes) of the given node"""
        
    def _stop_iteration(self, node, depth):
        """
        @return True for `node` at `depth` to stop the search 
        in that direction. The respective node will not be returned either."""
        return False
        
    def _prune_node(self, node, depth):
        """@return True if `node` at `depth` be pruned from result, so that it is not returned"""
        return False
        
    def _iter_(self, root_node, direction, traversal_type):
        """
        @return iterator yielding tuples with (level, node), where the level indicates number of nodes between
        the the root node and the returned `node`.
        @param root_node the node with which to start the iteration
        @param direction specifies search direction, either `upstream` or `downstream`, which are provided
        as constants on this type.
        @param traversal_type one of the constants in `traversal_types`, either `breadth_first` or `depth_first` 
        """
        # VERIFY INPUT 
        assert direction in self.directions, "invalid direction: %s" % direction
        assert traversal_type in self.traversal_types, "invalid traversal type: %s" % traversal_type
        
        # PREPARE ALGORITHM
        visited = set()
        stack = deque()
    
        if traversal_type == self.breadth_first:
            add_to_stack = lambda nlist, depth: stack.extendleft((depth, node) for node in reversed(nlist))
            #end addToStck brnach first
        else:
            add_to_stack = lambda nlist, depth: stack.extend((depth, node) for node in nlist)
        #end obtain add_to_stack function
    
        # adjust function to define direction
        if direction == self.downstream:
            nodes_in_direction = self._successors
        else:
            nodes_in_direction = self._predecessors
        #end obtain direction
        
        if self.skip_root_node:
            add_to_stack(nodes_in_direction(root_node), 1)
        else:
            stack.append((0, root_node))
        #end skip root node from result
        
        stop = self._stop_iteration
        prune = self._prune_node
        visit_once = self.visit_once
        max_depth = self.max_depth
        
        # NON-RECURSIVE SEARCH
        while stack:
            depth, node = stack.pop()               # depth of node, node
    
            if node in visited:
                continue
            #end handle visit_once
    
            if visit_once:
                visited.add(node)
            #end update visited
    
            if stop(node, depth):
                continue
            #end handle stop iteration
    
            if not prune(node, depth):
                yield node, depth
            #end yield node
    
            # only continue to next level if this is appropriate !
            new_depth = depth + 1
            if max_depth > -1 and new_depth > max_depth:
                continue
            #end skip node if depth level is reached
    
            add_to_stack(nodes_in_direction(node), new_depth)
        # END for each item on work stack
        
    ## -- End Subclass Methods -- @}


class DictObject(object):
    """An object which wraps a dictionary to allow object.key access.
    If the source dictionary doesn't contain any sub-dictionaries, the input 
    dict will be referenced. Otherwise it will be copied.
    
    An attribute error is raised if a value is not accessible.
    
    Please note that you cannot access dict keys which are not valid attribute names.
    """
    
    _default_dict = dict()
    
    def __init__(self, indict = _default_dict):
        """Initialize this instance from an input dictionary. If it contains other dictionaries, those will 
        trigger their parent dictionaries to be copied, as they will be used as DictObject themselves and 
        placed in the copy accordingly.
        NOTE: other DictObjects are used by reference. Generally, this type tries to perform the least
        amount of copying possible."""
        if indict is self._default_dict:
            return
        # end handle default instantiation, which makes us empty
        if isinstance(indict, DictObject):
            self.__dict__ = indict.__dict__
            return
        #END handle special case, be a reference
        dct = indict
        unpackable_types = (dict, tuple, list)
        for key, val in dct.iteritems():
            if isinstance(val, unpackable_types):
                dct = None
                break
        #END for each key-value pair
        
        if dct is None:
            dct = dict(indict)
            def unpack(val):
                """unpack helper"""
                if isinstance(val, dict):
                    val = DictObject(val)
                elif isinstance(val, (tuple, list)):
                    val = type(val)(unpack(item) for item in val)
                return val
            #END unpack
            for key, val in dct.iteritems():
                dct[key] = unpack(val)
            #END for each k,v pair
        #END handle recursive copy
        self.__dict__ = dct
        
    def __str__(self):
        return pprint.pformat(self.__dict__)
        
    def __repr__(self):
        return str(self)
        
    def __getattr__(self, name):
        return object.__getattribute__(self, name)
        
    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            raise KeyError(name)
        #end convert exception
        
    def __setitem__(self, name, value):
        setattr(self, name, value)
        
    def __contains__(self, name):
        return name in self.__dict__
    
    def __len__(self):
        return len(self.__dict__)
        
    def __iter__(self):
        return iter(self.__dict__)
        
    def __eq__(self, other):
        """Compares a possibly expensive comparison"""
        if isinstance(other, DictObject):
            # EXPENSIVE !
            return self.to_dict() == other.to_dict()
        elif isinstance(other, dict):
            return self.to_dict() == other
        # end handle type of other
        return self is other
        
    
    # R0912 Too many branches - yes, he is right, however, its how it is - don't want to put 
    # the utilty methods external
    # pylint: disable-msg=R0912
    def to_dict(self, recursive = False):
        """@return ourselves as normal dict
        @param recursive if True, a recursive copy will be returned if required."""
        if recursive:
            def obtain_needs_copy(value):
                """figure out if a copy is required"""
                if isinstance(value, DictObject):
                    return True
                if isinstance(value, (tuple, list, set)):
                    for item in value:
                        if obtain_needs_copy(item):
                            return True
                        #end check needs copy
                    #end for each item in value
                #end if instance is iterable
                return False
            #end check needs copy
            
            # W0631 Using possibly undefined loop variable , val, its defined ... 
            # R0912 Too many branches - yes, he is right, however, its how it is - don't want to put 
            # the utilty methods external
            # pylint: disable-msg=W0631
            def unpack(val):
                """unpack val recursively and copy it gently"""
                if isinstance(val, DictObject):
                    val = val.to_dict(recursive)
                elif isinstance(val, (tuple, list, set)):
                    val = type(val)(unpack(item) for item in val)
                #end handle type resolution
                return val
            #end unpack
            
            needs_copy = False
            for value in self.__dict__.itervalues():
                if obtain_needs_copy(value):
                    needs_copy = True
                    break
                #end check value
            #END for each value
            
            if needs_copy:
                new_dict = dict()
                for key, val in self.__dict__.iteritems():
                    new_dict[key] = unpack(val)
                #END for each key, value pair
                return new_dict
            # else:
            #   just fall through and return ourselves as dictionary
            
        #END handle recursion
        return self.__dict__
        
    def clone(self):
        """@return a deep copy of this dict. This onyl means that the key-sets are independent. However, the 
        values are still shared, which matters in case of lists for instance"""
        return type(self)(deepcopy(self.to_dict(recursive=True)))
        
    def inversed_dict(self):
        """@return new dictionary which uses this dicts keys as values, and values as keys
        @note duplicate values will result in just a single key, effectively drupping items.
        Use this only if you have unique key-value pairs"""
        return dict(zip(self.__dict__.values(), self.__dict__.keys()))
    
    def get(self, name, default=None):
        """as dict.get"""
        return self.__dict__.get(name, default)
        
    def keys(self):
        """as dict.keys"""
        return self.__dict__.keys()
        
    def values(self):
        """as dict.values"""
        return self.__dict__.values()
        
    def items(self):
        """as dict.items"""
        return self.__dict__.items()
        
    def iteritems(self):
        """as dict.iteritems"""
        return self.__dict__.iteritems()


# W0231 _init__ method from base class 'dict' is not called - in this case it shouldn't be called actually
# pylint: disable-msg=W0231

class OrderedDict(dict, DictMixin):
    """@copyright (c) 2009 Raymond Hettinger

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation files
    (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge,
    publish, distribute, sublicense, and/or sell copies of the Software,
    and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:
    
    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
    
    @note: Unfortunately, there is no unit test for this available or I didn't
    find it. As its the default python implementation though, I believe it
    should be working pretty well.
    """
    __slots__ = ('_map', '_end')
    
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        self.clear() # reset
        self.update(*args, **kwds)

    def clear(self):
        end = list()
        object.__setattr__(self, '_end', end)
        object.__setattr__(self, '_map', dict()) # key --> [key, prev, next]
        end += [None, end, end]         # sentinel node for doubly linked list
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self._end
            curr = end[1]
            curr[2] = end[1] = self._map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next_item = self._map.pop(key)
        prev[2] = next_item
        next_item[1] = prev

    def __iter__(self):
        end = self._end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self._end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        """same as in dict"""
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    # E0203 it thinks _map and _end are created after their definition, which is not true
    # pylint: disable-msg=E0203
    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = (self._map, self._end)
        del self._map, self._end
        inst_dict = vars(self).copy()
        self._map, self._end = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)
        
    def __getattr__(self, name):
        """provides read access"""
        try:
            return self[name]
        except KeyError:
            raise AttributeError("No attribute named '%s'" % name)
        #end handle getitem
        
    def __setattr__(self, name, value):
        """Set the given value into our dict"""
        if name in self.__slots__:
            return super(OrderedDict, self).__setattr__(name, value)
        self[name] = value

    def keys(self):
        """same as in dict"""
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems

    def __str__(self, indent=1):
        indent_str = '    '*indent
        ret_str = "Dict\n"
        for key, value in self.iteritems():
            if isinstance(value, OrderedDict):
                ret_str += "%s%s: %s" % (indent_str, key, value.__str__(indent=indent+1))
            else:
                ret_str += "%s%s: %s\n" % (indent_str, key, str(value))

        return ret_str

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, self.items())

    def copy(self):
        """same as in dict"""
        return self.__class__(self)
        
    def to_dict(self):
        """@return a recursive copy of this dict, except that the dict type is just dict.
        @note useful for pretty-printing"""
        out = dict()
        for key, value in self.iteritems():
            if isinstance(value, self.__class__):
                value = value.to_dict()
            out[key] = value
        #end for each key-value pair
        return out

    @classmethod
    def fromkeys(cls, iterable, value=None):
        """same as in dict"""
        new_dict = cls()
        for key in iterable:
            new_dict[key] = value
        return new_dict

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            if len(self) != len(other):
                return False
            for left, right in  zip(self.items(), other.items()):
                if left != right:
                    return False
            return True
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other


class Version(object):
    """An RPM-like version implementation, which doesn't make assumptions, yet allows comparison of arbitraty 
    strings.
    This type will also allow to analyse version strings and could server as a base class for more constraint
    version types.
    
    Non-alphanumeric characters are used as separator between tokens, each token serving as sub-version
    
    Comparisons are implemented using the 
    [RPM comparison algorithm](http://fedoraproject.org/wiki/Archive:Tools/RPM/VersionComparison)
    
    ## Examples ####
    
    * 2012.2.0
    * 1.2.3-R1
    * 20
    * foo.bar
    """
    __slots__ = ('_version')

    _re_tokens = re.compile('[0-9]+|[a-zA-Z]+')
    
    # -------------------------
    ## @name Configuration
    # @{
    
    TOKEN_ANY = "any"
    TOKEN_STRING = "string"
    TOKEN_NUMBER = "number"
    
    ## Represents an unknown version, and default instance are intiialized with it
    UNKNOWN = 'unknown'
    
    ## -- End Configuration -- @}
    
    def __init__(self, version_string = UNKNOWN):
        """Intiialize this instance
        @param version_string a string of pretty much any format that resembles a version. Usually, it consists
        of digits and/or names"""
        assert isinstance(version_string, basestring), '%s was %s, require string' % (version_string, type(version_string))
        self._version = version_string
        
        
    def _tokens(self):
        """@return a list of all tokens, dot separated"""
        return self._re_tokens.findall(self._version)
        
    # -------------------------
    ## @name Protocols
    # @{
    
    def __hash__(self):
        """brief docs"""
        return hash(self._version)
    
    def __cmp__(self, rhs):
        """Compare ourselves with the other version or string using 
        [RPM comparison algorithm](http://fedoraproject.org/wiki/Archive:Tools/RPM/VersionComparison)"""
        if not isinstance(rhs, type(self)):
            rhs = type(self)(rhs)
        # assure type
        
        lts, rts = self._tokens(), rhs._tokens()
        for lt, rt in zip(lts, rts):
            if isinstance(lt, int):
                if isinstance(rt, int):
                    if lt == rt:
                        continue
                    else:
                        return cmp(lt, rt)
                    # handle int comparison
                else:
                    # strings are always older compared to ints
                    return 1
                # handle rt type
            else:
                if isinstance(rt, basestring):
                    if lt == rt:
                        continue
                    else:
                        return cmp(lt, rt)
                    # end string handle comparison
                else:
                    # ints are always newer
                    return -1
                # end handle rt type
            # end handle lt type
        # end for each token
        
        # still here ? compare the length - more tokens are better
        cmp_len = cmp(len(lts), len(rts))
        if cmp_len != 0:
            return cmp_len
        # end 
        
        # equality !
        return 0
        
    def __str__(self):
        return self._version
    
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self._version)
        
    def __getitem__(self, index):
        """@return version token at the given index. Type can be integer or string"""
        return self.tokens()[index]
        
    ## -- End Protocols -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def tokens(self, token_type = TOKEN_ANY):
        """@return list of tokens of the given type that this version is comprised of
        @note any number will be returned, even if it is part of a string"""
        assert token_type in (self.TOKEN_ANY, self.TOKEN_STRING, self.TOKEN_NUMBER)
        tokens = self._tokens()
        
        res = list()
        for token in self._tokens():
            try:
                number = int(token)
                if token_type in (self.TOKEN_NUMBER, self.TOKEN_ANY):
                    res.append(number)
                # end handle number type
            except ValueError:
                if token_type in (self.TOKEN_STRING, self.TOKEN_ANY):
                    res.append(token)
                # end handle string type
            # end handle exception
        # end for each token
        return res
        
    ## -- End Interface -- @}
    
# end class Version


class Singleton(object) :
    """ Singleton classes can be derived from this class,
        you can derive from other classes as long as Singleton comes first (and class doesn't override __new__) """
    def __new__(cls, *p, **k):
        # explicitly query the classes dict to allow subclassing of singleton types.
        # Querying with hasattr would follow the inheritance graph
        if '_the_instance' not in cls.__dict__:
            cls._the_instance = super(Singleton, cls).__new__(cls)
        return cls._the_instance


class StringChunker(object):
    """A utility to split an indexed object into chunks of a given size and distribute them
    in named keys of a dictionary"""

    __slots__ = (
                    '_last_key'
                )

    ## Characters we use for string generation
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self):
        self._last_key = self.chars[0]

    # -------------------------
    ## @name Utilities
    # @{

    def _gen_key(self, out):
        """Generate a key which doesn't yet exist in out"""
        key = self._last_key
        while key in out:
            index = self.chars.index(key[0]) + 1
            if index == len(self.chars):
                key = self.chars[0] + key
                index = 0
            # end append new character
            key = self.chars[index] + key[1:]
        # end increment key
        self._last_key = key
        return key
        
    
    ## -- End Utilities -- @}

    def split(self, string, chunk_size, out):
        """Split string into chunks of size chunk_size and place them into unique keys of the out 
        dictionary.
        @param string to split
        @param chunk_size size of chunks in bytes (or indices, if you so will)
        @param out dictionary that will be filled with chunks, whose keys will be returned by this method 
        in order.
        @return an ordered list of keys pointing to the chunks, which can be re-assembled in the given order
        """
        keys = list()
        for start_index in range(0, len(string), chunk_size):
            key = self._gen_key(out)
            out[key] = string[start_index:start_index + chunk_size]
            keys.append(key)
        # end for each chunk
        return keys


class Thread(threading.Thread):
    """Applies a few convenience fixes"""
    __slots__ = ()

    def start(self):
        """Start the thread
        @return self"""
        super(Thread, self).start()
        return self
        
# end class Thread


class ConcurrentRun(Thread):
    """Execute a function in its own thread and provide the result.
    Note: Currently this is implemented such that each run starts its own thread, 
    which is expensive. For many concurrent operations, a thread pool should be used
    
    Usage: ConcurrentRun(my_method).start().result() or
    ConcurrentRun(my_method).start() # and forget about it

    @note python will terminate even though a concurrent 
    """
    
    __slots__ = (
                '_result',  # result of our operation
                '_exc',     # the exception thrown
                '_fun',     # method to run
                '_log',     # optional logger instance
                )
    
    def __init__(self, fun, logger = None, daemon=False):
        """Initialize this instance with the function to execute
        @param fun callable to execute
        @param logger a logger instance
        @param daemon if True, a running Thread will prevent python to exit"""
        super(ConcurrentRun, self).__init__()
        self.daemon = daemon
        self._result = None
        self._exc = None
        self._fun = fun
        self._log = logger
        
    def _assure_joined(self):
        try:
            self.join()
        except RuntimeError: # on joining before started
            pass
        #END handle exception
        
    def run(self):
        try:
            self._result = self._fun()
        except Exception, exc:
            self._exc = exc
            if self._log is not None:
                self._log.critical("%s failed" % str(self._fun), exc_info=1)
            #END log errors
        #END handle exception
        
    #{ Interface
    
    def result(self):
        """@return the result of the function we ran. Will block until we are done
        with our computation"""
        self._assure_joined()
        return self._result
    
    def error(self):
        """@return exception thrown or None if there was no error"""
        self._assure_joined()
        return self._exc
    
    #} END interface
    

class ProgressIndicator(object):
    """A base allowing to track progress information
    The default implementation just prints the respective messages
    Additionally you may query whether the computation has been cancelled by the user
    
    @note this interface is a simple progress indicator itself, and can do some computations
    for you if you use the get() method yourself"""

    __slots__ = (
                    '_progress_value',
                    '_min',
                    '_max',
                    '_rr',
                    '_relative',
                    '_may_abort'
                )


    #{ Initialization

    def __init__(self, min = 0, max = 100, is_relative = True, may_abort = False, round_robin=False, **kwargs):
        """@param min the minimum progress value
        @param max the maximum progress value
        @param is_relative if True, the values given will be scaled to a range of 0-100,
            if False no adjustments will be done
        @param may_abort if True, the progress can be used to ask for aborting the underlying action
        @param round_robin see `set_round_robin` 
        @param kwargs additional arguments being ignored"""
        self.set_range(min, max)
        self.set_relative(is_relative)
        self.set_abortable(may_abort)
        self.set_round_robin(round_robin)
        self._progress_value = min

    def begin(self):
        """intiialize the progress indicator before calling `set` """
        self._progress_value = self._min        # refresh

    def end(self):
        """indicate that you are done with the progress indicator - this must be your last
        call to the interface"""
        pass

    #} END initialization

    #{ Edit
    
    def refresh(self, message = None):
        """Refresh the progress indicator so that it represents its values on screen.
        
        @param message message passed along by the user"""
        # To be implemented in subclass

    def set(self, value, message = None , omit_refresh=False):
        """Set the progress of the progress indicator to the given value
        
        @param value progress value (min<=value<=max)
        @param message optional message you would like to give to the user
        @param omit_refresh by default, the progress indicator refreshes on set,
            if False, you have to call refresh manually after you set the value"""
        self._progress_value = value

        if not omit_refresh:
            self.refresh(message = message)

    def set_range(self, min, max):
        """set the range within we expect our progress to occour"""
        self._min = min
        self._max = max
        
    def set_round_robin(self, round_robin):
        """Set if round-robin mode should be used. 
        If True, values exceeding the maximum range will be wrapped and 
        start at the minimum range""" 
        self._rr = round_robin

    def set_relative(self, state):
        """enable or disable relative progress computations"""
        self._relative = state

    def set_abortable(self, state):
        """If state is True, the progress may be interrupted, if false it cannot
        be interrupted"""
        self._may_abort = state

    def setup(self, range=None, relative=None, abortable=None, begin=True, round_robin=None):
        """Multifunctional, all in one convenience method setting all important attributes
        at once. This allows setting up the progress indicator with one call instead of many
        
        @note If a kw argument is None, it will not be set
        @param range Tuple(min, max) - start ane end of progress indicator range
        @param relative equivalent to `set_relative`
        @param abortable equivalent to `set_abortable`
        @param round_robin equivalent to `set_round_robin`
        @param begin if True, `begin` will be called as well"""
        if range is not None:
            self.set_range(range[0], range[1])

        if relative is not None:
            self.set_relative(relative)

        if abortable is not None:
            self.set_abortable(abortable)
            
        if round_robin is not None:
            self.set_round_robin(round_robin)

        if begin:
            self.begin()

    #} END edit

    #{ Query

    def get(self):
        """@return the current progress value
        
        @note if set to relative mode, values will range
            from 0.0 to 100.0.
            Values will always be within the ones returned by `range`"""
        p = self.value()
        mn,mx = self.range()
        if self.round_robin():
            p = p % mx
                
        if not self.is_relative():
            return min(max(p, mn), mx)
        # END relative handling 
        
        # compute the percentage
        return min(max((p - mn) / float(mx - mn), 0.0), 1.0) * 100.0
        
    def value(self):
        """@return current progress as it is stored internally, without regarding 
            the range or round-robin options.
            
        @note This allows you to use this instance as a counter without concern to 
            the range and round-robin settings"""
        return self._progress_value

    def range(self):
        """@return tuple(min, max) value"""
        return (self._min, self._max)

    def round_robin(self):
        """@return True if round_robin mode is enabled"""
        return self._rr

    def prefix(self, value):
        """
        @return a prefix indicating the progress according to the current range
            and given value """
        prefix = ""
        if self.is_relative():
            prefix = "%i%%" % value
        else:
            mn,mx = self.range()
            prefix = "%i/%i" % (value, mx)

        return prefix

    def is_abortable(self):
        """@return True if the process may be canceled"""
        return self._may_abort

    def is_relative(self):
        """
        @return true if internal progress computations are relative, False if
            they are treated as absolute values"""
        return self._relative

    def is_cancel_requested(self):
        """@return true if the operation should be aborted"""
        return False

    #} END query

