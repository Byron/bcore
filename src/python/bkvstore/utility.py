#-*-coding:utf-8-*-
"""
@package bkvstore.utility
@brief Various utilities for use in the kvstore

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['KVStringFormatter']

import sys
from string import Formatter


class KVStringFormatter(Formatter):
    """A formatter which introduces a way to specify the type to convert to. That way, it is possible to use
    more native attribute-access semantics in format strings.

    Examples
    ========

    The example below would fail as for the system, the value at 'path' will only be a string.
    Even though the KeyValueStoreSchema will know about the type, it only knows about desired types
    in a particular portion of the tree for which values are retrieved. As the format syntax can reference
    any value, our small schema won't help.

        '{path.dirname}'

    This is why - and that's a good thing - the user has to specify the desired type natively as part of 
    the format string, which acts as a hint on the type to use.

        '{path.as_KVPath.dirname}'

    The example above will use the 'as_' prefix as a hint for desired conversion. The following text, 'KVPath'
    is interpreted as a type name which is looked for in all currently loaded modules.

    When found once, the result is cached for later.

    Customization
    =============

    It is possible for users to adjust this type 'globally' to provide a fallback mechanism for AttributeErrors.
    That way, it is possible to say something like: if 'foo.name.attr' doesn't have 'attr', lookup 'name' in our
    custom mapping to possibly convert it to a given type.

    Doing this will create special cases, as it will miraculously work just for the configured key names.

    """
    __slots__ = ()

    ## Mapping from type-name to type
    _type_cache = dict()
    ## Mapping from key name to type (configured by users)
    _custom_types = dict()

    # -------------------------
    ## @name Utilities
    # @{

    @classmethod
    def _type_by_name(cls, name):
        """@return the type matching the given name, possibly looking it up in our type cache
        @throws ValueError in vase there is no matching type"""
        try:
            return cls._type_cache[name]
        except KeyError:
            # cache miss - search in modules and update cache
            for mod in sys.modules.values():
                try:
                    typ = getattr(mod, name)
                except AttributeError:
                    continue
                # end ignore misses

                cls._type_cache[name] = typ
                return typ
            # end for each module

            raise ValueError("No type found matching name '%s'" % name)
        # end handle cache

    ## -- End Utilities -- @}

    def get_field(self, field_name, args, kwargs):
        """This is just a copy of the base implementation, re-implementing the portion we need"""
        first, rest = field_name._formatter_field_name_split()
        try:
            obj = self.get_value(first, args, kwargs)
        except Exception:
            raise AttributeError("Couldn't find value named '%s'" % first)
        # end be a bit better here

        # loop through the rest of the field_name, doing
        #  getattr or getitem as needed
        prev_attr = None
        for is_attr, attr in rest:
            if is_attr:
                if attr.startswith('as_'):
                    obj = self._type_by_name(attr[3:])(obj)
                else:
                    try:
                        obj = getattr(obj, attr)
                    except AttributeError:
                        if prev_attr not in self._custom_types:
                            raise
                        # end re-raise if key is unknown
                        # this may re-raise, but in that case we don't have to care
                        obj = getattr(self._custom_types[prev_attr](obj), attr)
                    # end try special values
                # end handle attribute
            else:
                obj = obj[attr]
            # end handle is_attr
            prev_attr = attr
        # end for each attribute

        return obj, first

    # -------------------------
    ## @name Interface
    # @{

    @classmethod
    def set_key_type(cls, key_name, type):
        """Associate the given type with the key_name.
        That way, whenever key_name.attr fails, the mapping will be used to convert the value as key_name to 
        the desired type, retrying the attribute access"""
        assert '.' not in key_name
        cls._custom_types[key_name] = type

    @classmethod
    def set_key_type_by_schema(cls, schema, keys, sep='.'):
        """Similar to set_key_type(), but works with a schema to obtain the desired types
        @param schema a KeyValueStoreSchema instance
        @param keys an iterable of keys to obtain from the schema. It is valid to for keys to be contain
        the key-separator sep, in which case only the last sub-key will be added as key's type.
        For instance, if the key is foo.bar.baz=Path, it the mapping will be 'baz=Path'.
        We handle all schema values correctly.
        @return this type
        """
        for key in keys:
            typ = schema
            for token in key.split(sep):
                typ = typ[token]
            # end for each item
            # they are expected to have a default constructor
            if callable(typ):
                typ = type(typ())
            else:
                typ = type(typ)
            # end 
            assert isinstance(typ, type), "failed to resolve schema type: %s" % typ
            cls.set_key_type(token, typ)
        # end for each key
        return cls
    
    ## -- End Interface -- @}


    

# end class KVStringFormatter
