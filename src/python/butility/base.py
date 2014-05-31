#-*-coding:utf-8-*-
"""
@package butility.base
@brief Most fundamental base types

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division

from minifuture import with_metaclass
__all__ = ['Error', 'Interface', 'Meta', 'abstractmethod', 
           'NonInstantiatable', 'is_mutable', 'smart_deepcopy', 'wraps', 'GraphIterator',
           'Singleton', 'LazyMixin', 'capitalize', 'equals_eps', 'tagged_file_paths', 'TRACE',
           'set_log_level', 'partial', 'parse_key_value_string', 'parse_string_value', 'size_to_int',
           'frequncy_to_seconds', 'int_to_size_string', 'load_package', 'load_files', 'load_file']

from functools import (wraps,
                       partial)
import logging
import os
import sys
import imp

from abc import (abstractmethod,
                 ABCMeta)

from copy import deepcopy
from itertools import chain
from collections import deque

from .path import Path

log = logging.getLogger('butility.base')


# ==============================================================================
## @name Constants
# ------------------------------------------------------------------------------
## @{

container_types = (list , set, tuple)

## The TRACE log level, between DEBUG and INFO
TRACE = int((logging.INFO + logging.DEBUG) / 2)

## -- End Constants -- @}


# ==============================================================================
## @name Logging
# ------------------------------------------------------------------------------
## @{

## Adjust logging configuration
# It's basically setup that will be there whenever someone uses the basic parts of the core package#
# That's how it should be though, TRACE should be there, and code relies on it.
setattr(logging, 'TRACE', TRACE)
logging.addLevelName(TRACE, 'TRACE')


def set_log_level(logger, level):
    """Set the loggers and its handlers log level to the given one"""
    for handler in logger.handlers:
         handler.setLevel(level)
    logger.setLevel(level)

## -- End Logging -- @}




# ==============================================================================
## \name Exceptions
# ------------------------------------------------------------------------------
# Basic Exception Types
## \{

class Error(Exception):
    """Most foundational framework exception"""
    __slots__ = ()

# end class Error
## -- End Exceptions -- \}


# ==============================================================================
## @name Routines
# ------------------------------------------------------------------------------
## @{

def is_mutable( value):
    """Recursively check if the given value is mutable.
    
    A value is considered mutable if at least one contained value is mutable
    @param value a possibly nested value of built-in types
    @return true if value is mutable"""
    if isinstance(value, (str, int, float, type(None))):
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

def equals_eps(float_left, float_right, epsilon = sys.float_info.epsilon):
    """@return True if float_left equals float_right within an error of epsilon"""
    return abs(float_left - float_right) <= epsilon

def parse_string_value(string):
    """@return the actual numeric instance the value string represents. May be a list, if it starts 
    with '['."""
    if string.startswith('['):
        try:
            return eval(string)
        except Exception:
            raise ValueError("Failed to parse '%s' as a list" % (string))
        # end handle conversion
    # end handle lists

    if string in ('on', 'yes', 'true', 'True'):
        return True
    if string in ('off', 'no', 'false', 'False'):
        return False
    
    # more conversions are not required, as they are handled by the schema
    return string

def parse_key_value_string(string, separator='='):
    """@return tuple(key, value), whereas key is what's on the left side of the separator, and value 
    is either a numerical value, string, or list of scalars
    @param string the k{separator}v string to parse
    @param separator
    @throws ValueError if string is malformatted"""
    if len(string) < 2 or separator not in string:
        raise ValueError("expected k=v string, got '%s'" % string)
    # end 

    k, v = string.split(separator)
    return k, parse_string_value(v)


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

    The list of file-paths (bapp.path instances) returned would be all matching files from the global path and
    all matching files from the local one, sorted such that the file with the smallest amount
    of tags come first, files with more tags (more specialized ones) will come after that. 

    @param directory iterable of directory paths to look in for files, or a single directory
    @param taglist list or tuple of tags of tags, like a tag for the operating system, or the user name, e.g.
    ('win', 'project', 'maya')
    @param pattern simple fnmatch pattern as used for globs or a list of them (allowing to match several
        different patterns at once)
    @return list of matches file paths (as mrv Path)
    """
    log.debug('obtaining tagged files from %s, tags = %s', directory, ', '.join(taglist))
    
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


def load_package(package_directory, module_name):
    """unconditionally Imports a package, which is described by a path to a directory
    @param package_directory a folder containing an __init__.py[co] file 
    @param module_name the name of the module in sys.modules
    @return the imported module object"""
    imp.load_module(module_name, None, str(package_directory), ('', '', imp.PKG_DIRECTORY))
    return sys.modules[module_name]


def _load_files(path, files, on_error):
    """load all python \a files from \a path
    @return list of loaded files as full paths"""
    res = list()
    def py_filter(f):
        return f.endswith('.py') and not \
               f.startswith('__')
    # end filter

    for filename in filter(py_filter, files):
        py_file = os.sep.join([path, filename])
        (mod_name, _) = os.path.splitext(os.path.basename(py_file))
        try:
            load_file(py_file, mod_name)
        except Exception:
            log.error("Failed to load %s from %s", mod_name, py_file, exc_info=True)
            on_error(py_file, mod_name)
        else:
            log.info("loaded %s into module %s", py_file, mod_name)
            res.append(py_file)
        # end handle result
    # end for eahc file to load
    return res

def load_files(path, recurse=False, on_error=lambda f, m: None):
    """Load all .py files found in the given directory, or load the file it points to
    @param path either path to directory, or path to py file.
    @param recurse if True, path will be searched for usable files recursively
    @param on_error f(py_file, module_name) => None to perform an action when importing a module 
    fails. It may raise to abort the entire operation. Note that an exception is set when called.
    @return a list of files loaded successfully"""
    # if we should recurse, we just use the standard dirwalk.
    # we use topdown so top directories should be loaded before their
    # subdirectories and we follow symlinks, since it seems likely that's
    # what people will expect
    res = list()
    path = Path(path)
    if path.isfile():
        res += _load_files(path.dirname(), [path.basename()], on_error)
    else:
        seen = None
        for seen, (path, dirs, files) in enumerate(os.walk(path, topdown=True, followlinks=True)):
            res += _load_files(path, files, on_error)
            if not recurse:
                break
            # end handle recursion
        # end for each directory to walk
        if seen is None:
            log.log(logging.TRACE, "Didn't find any plugin files at '%s'", path)
        # end 
    # end handle file or directory
    return res
    
def load_file(python_file, module_name):
    """Load the contents of the given python file into a module of the given name.
    If the module is already loaded, it will be reloaded
    @return the loaded module object
    @throws Exception any exception raised when trying to load the module"""
    imp.load_source(module_name, str(python_file))
    return sys.modules[module_name]

## -- End Filesystem Utilities -- @}

## -- End Routines -- @}


# ==============================================================================
## \name Meta-Classes
# ------------------------------------------------------------------------------
# Our basic meta classes which allow us to manipulate all class level functions
# at will to automated otherwise tedious processes.
## \{

class Meta(ABCMeta):
    """A base class for all other meta-classes used in the @ref bapp package.
    
    It provides facilities to automatically wrap methods into decorators which 
    perform certain tasks, like additional logging for improved debugging.
    
    * All subclasses of Interface are put into bapp as well, allowing their access
      through bapp.InterfaceName.
    * Puts new types into bapp if the type itself (not its subtype) has the 'place_into_root_package' set to True
    """
    
    # -------------------------
    ## @name Subclass Interface
    # Methods for use by subclasses
    # @{
    
    @classmethod
    def _class_attribute_value(cls, clsdict, bases, attribute):
        """@return value found at clsdict[attribute] or bases.mro().__dict__[attribute] in standard search
        order, or None if nothing was found.
        @note useful if you store information for digestion by your metaclasson on the  type itself, or 
        on base classes of that type. This method basically emulates inheritance.
        @param cls
        @param clsdict
        @param bases
        @param attribute string identifying the attribute in the class dicts to look at"""
        def iterate_clsdicts():
            for base in bases:
                for mro_cls in base.mro():
                    yield mro_cls.__dict__
            # end for each base
        # end for each 
        
        # iterate top down
        for cls_dict in reversed(list(chain(iterate_clsdicts(), (clsdict, )))):
            rval = cls_dict.get(attribute)
            if rval:
                return rval
        # end for each clsdict to iterate
        
        return None
        
    ## -- End Subclass Interface -- @}
    
# end class Meta

## -- End Meta-Classes -- \}


# ==============================================================================
## \name Mixins
# ------------------------------------------------------------------------------
# A category of classes from which you can derive to add a certain interface
# to your type. You might have to implement some protocol methods though,
# depending on the actual mixin.
## \{


class LazyMixin(object):
    """Base class providing an interface to lazily retrieve attribute values upon
    first access. This is efficient as objects can be created without causing
    overhead at creation time, delaying necessary overhead to the time the
    respective attribute is actually used.
    
    If slots are used, memory will only be reserved once the attribute
    is actually accessed and retrieved the first time. All future accesses will
    return the cached value as stored in the Instance's dict or slot.
    
    Here is how you implement your subtype
    @snippet bapp/tests/doc/test_examples.py LazyMixinExample Implementation
    
    In code, you can use the lazy attributes natively, its entirely transparent
    to the caller.
    Ideally, this system is used for internal attributes which will be set on first
    use, maybe by reading from a file or a slow device.
    
    @snippet bapp/tests/doc/test_examples.py LazyMixinExample Example
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


# ==============================================================================
## \name Basic Types
# ------------------------------------------------------------------------------
# Implementations for types suitable to serve as base for derived types 
## \{

class Interface(with_metaclass(Meta, object)):
    """base class for all interfaces"""
    
    ## Slots help to protect against typos when assigning variables, keep instances small, and document the
    ## types member variables
    __slots__ = tuple()
    
    def supports(self, interface_type):
        """@return True if this instance supports the interface of the given type
        @param interface_type type of the interface/class you require this instance to be derived from, or a 
        tuple of interfaces or classes
        @note useful if you only have a weak reference of your interface instance
        or proxy which is a case where the ordinary `isinstance(obj, iInterface)`
        will not work"""
        return isinstance(self, interface_type)


class NonInstantiatable(object):
    """A mixin which will makes it impossible to instantiate derived types
    
    @throws TypeError if someone tries to create an instance"""
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        """Prevents instantiation"""
        raise TypeError("This type cannot be instantiated")

# end class NonInstantiatable


class Singleton(object) :
    """ Singleton classes can be derived from this class,
        you can derive from other classes as long as Singleton comes first (and class doesn't override __new__) """
    def __new__(cls, *p, **k):
        # explicitly query the classes dict to allow subclassing of singleton types.
        # Querying with hasattr would follow the inheritance graph
        if '_the_instance' not in cls.__dict__:
            cls._the_instance = super(Singleton, cls).__new__(cls)
        return cls._the_instance


# end class Singleton


class GraphIterator(with_metaclass(Meta, object)):
    """A generic, none-recursive implementation of a graph-iterator, which is able to handle cycles.
    
    Its meant to be subclassed to make the interface more approachable
    @attention this approach is only useful if you don't care about the order or of your nodes are able
    to provide all the information you like right away (like information about the parent)
    @todo add a test for this type - its not even indirectly used yet. Alternatively, remove it if its not used
    by anybody"""
    __slots__ = ()
    
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
    
    @abstractmethod
    def _successors(self, node):
        """@return an iterable of successor nodes (i.e. output nodes) of the given node"""
        
    @abstractmethod
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

## -- End Basic Types -- \}



# ==============================================================================
## @name Unit Conversion Utilities
# ------------------------------------------------------------------------------
## @{

data_unit_multipliers = {
                'k' : 1024,
                'm' : 1024**2,
                'g' : 1024**3,
                't' : 1024**4,
                'p' : 1024**5,
                '%' : 1,
}

time_unit_multipliers = {
        's' : 1,
        'h' : 60**2,
        'd' : 60**2 * 24,
        'w' : 60**2 * 24 * 7,
        'm' : 60**2 * 24 * 30,
        'y' : 60**2 * 24 * 365
    }


def size_to_int(size):
    """Converts a size to the respective integer
    @param size string like 1M or 2T, or 35.5K
    """
    unit = size[-1].lower()
    if unit in '0123456789':
        return int(size)
    # end handle no unit
    try:
        return int(data_unit_multipliers[unit] * float(size[:-1]))
    except KeyError:
        raise ValueError("Invalid unit: '%s'" % unit)
    # end handle errors gracefully

def frequncy_to_seconds(time_string):
    """@return seconds identified by the given time-string, like 14s, or 14w
    @throw ValueError"""
    try:
        return int(time_string[:-1]) * time_unit_multipliers[time_string[-1].lower()]
    except (KeyError, ValueError):
        raise ValueError("Could not parse '%s' - should be something like <integer><unit>, like 14s, or 12d" % time_string)
    #end handle frequency conversion

def int_to_size_string(size):
    """@return a string suitable for input into size_to_int(), scaling dynamically depending on the actual `size`"""
    asize = abs(size)
    if asize < 1024**2:
        divider, unit = 1024, 'K'
    elif asize <1024**3:
        divider, unit = 1024**2, 'M'
    elif asize <1024**4:
        divider, unit = 1024**3, 'G'
    elif asize <1024**5:
        divider, unit = 1024**4, 'T'
    else:
        divider, unit = 1024**5, 'P'
    # end handle sizes
    return '%.2f%s' % (size / float(divider), unit)

## -- End Unit Conversion Utilities -- \}
