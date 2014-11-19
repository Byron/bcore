#-*-coding:utf-8-*-
"""
@package bkvstore.tests.base
@brief base types which are shared among test modules in this package

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = ['TestConfiguration']

import yaml


from butility.tests import TestCase
from butility import Path
from bkvstore import OrderedDictYAMLLoader


class TestConfiguration(TestCase):
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

    @classmethod
    def config_data(cls, name):
        """@return deserialized yaml dictionary with data from the given file
        using the OrderedDictYAMLLoader"""
        return yaml.load(open(cls.fixture_path(name)), Loader=OrderedDictYAMLLoader)

# end class TestConfiguration
