#-*-coding:utf-8-*-
"""
@package butility.properties.types
@brief Implements various types for using the Properties framework

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = ['PrefixProperty']

from .base import Property


class PrefixProperty(Property):
    """A Property which sets and gets values in its instance using a simple prefix
    
    This allows syntax like inst.foo.set_value(1) to set inst._foo to be 1.
    
    If used within CompoundProperties, the attribute names will contain underscores '_' in place of dots '.'
    
    @note this type is recommended to be used with slots to denote viable target attributes
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Prefix to use when getting and setting the actual property
    prefix = '_'
    
    ## -- End Configuration -- @}
    
    def _attr_name(self):
        """@return name of attribute to write to """
        return self.prefix + self._descriptor.name().replace('.', '_')
    
    def value(self):
        return getattr(self._instance, self._attr_name())

    def set_value(self, value):
        setattr(self._instance, self._attr_name(), value)
        return self
        
    def delete(self):
        delattr(self._instance, self._attr_name())
        
# end class PrefixProperty


