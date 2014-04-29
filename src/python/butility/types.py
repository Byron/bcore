#-*-coding:utf-8-*-
"""
@package butility.types
@brief A module with general purpose utility types

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['StringChunker', 'Version', 'OrderedDict', 'DictObject', 'ProgressIndicator', 'PythonFileLoader']

from UserDict import DictMixin
import imp
import sys
import os
import re
import pprint
import logging
from copy import deepcopy
from .path import Path

log = logging.getLogger(__name__)


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

    @property
    def major(self):
        """@return our major version"""
        return self[0]

    @property
    def minor(self):
        """@return our minor version"""
        return self[1]
        
    @property
    def patch(self):
        """@return our patch level"""
        return self[2]

    ## -- End Interface -- @}
    
# end class Version


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


class DictObject(object):
    """An object which wraps a dictionary to allow object.key access.
    If the source dictionary doesn't contain any sub-dictionaries, the input 
    dict will be referenced. Otherwise it will be copied.
    
    An attribute error is raised if a value is not accessible.
    
    Please note that you cannot access dict keys which are not valid attribute names.
    """
    
    _default_dict = dict()
    _unpackable_types = (dict, tuple, list)
    
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
        for key, val in dct.iteritems():
            if isinstance(val, self._unpackable_types):
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

# end class DictObject


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
        ret_str = "\n"
        for key, value in self.iteritems():
            if isinstance(value, OrderedDict):
                ret_str += "%s%s: %s" % (indent_str, key, value.__str__(indent=indent+1))
            elif isinstance(value, (tuple, list)):
                # for now, without recursion, assuming simple scalar values
                ret_str += "%s%s:\n" % (indent_str, key)
                for item in value:
                    ret_str += "%s - %s\n" % (indent_str, item)
                # end for each item
            else:
                ret_str += "%s%s: %s\n" % (indent_str, key, str(value))
            # end handle value type
        # end for each item in dict
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

# end class OrderedDict
    

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

# end clas ProgressIndicator


class PythonFileLoader(object):
    """ loads .py files from a given directory or load the given file, with recursion if desired
        @note it just loads the .py files"""
    __slots__ = ()
        
    @classmethod
    def _load_files(cls, path, files):
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
                cls.load_file(py_file, mod_name)
            except Exception:
                log.error("Failed to load %s from %s", mod_name, py_file, exc_info=True)
            else:
                log.info("loaded %s into module %s", py_file, mod_name)
                res.append(py_file)
            # end handle result
        # end for eahc file to load
        return res

    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def load_files(cls, path, recurse=False):
        """Load all .py files found in the given directory, or load the file it points to
        @param path either path to directory, or path to py file.
        @param recurse if True, path will be searched for usable files recursively
        @return a list of files loaded successfully"""
        # if we should recurse, we just use the standard dirwalk.
        # we use topdown so top directories should be loaded before their
        # subdirectories and we follow symlinks, since it seems likely that's
        # what people will expect
        res = list()
        path = Path(path)
        if path.isfile():
            res += cls._load_files(path.dirname(), [path.basename()])
        else:
            for path, dirs, files in os.walk(path, topdown=True, followlinks=True):
                res += cls._load_files(path, files)
                if not recurse:
                    break
                # end handle recursion
            # end for each directory to walk
        # end handle file or directory
        return res
        
    @classmethod
    def load_file(cls, python_file, module_name):
        """Load the contents of the given python file into a module of the given name.
        If the module is already loaded, it will be reloaded
        @return the loaded module object
        @throws Exception any exception raised when trying to load the module"""
        imp.load_source(module_name, python_file)
        return sys.modules[module_name]

    ## -- End Interface -- @}
# end class PythonFileLoader

