#-*-coding:utf-8-*-
"""
@package bkvstore.tests.test_schema
@brief tests for bkvstore.schema

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = []

from .base import TestConfiguration
from . import test_serialize


# Try * imports
from bkvstore.schema import *
from bdiff import RootKey
from bkvstore import YAMLKeyValueStoreModifier
from butility import wraps


def validator_backup(func):
    """Decorates func to temporarily store the global collector, and restore it aftwards"""
    @wraps(func)
    def wrapper(instance):
        """Backup global collector instance and restore it"""
        curr_collector = ValidatedKeyValueStoreSchema.collector()
        try:
            return func(instance)
        finally:
            ValidatedKeyValueStoreSchema.set_validator(curr_collector)
        # end assure collector gets reset
    # end wrapper
    return wrapper


class TestSchema(TestConfiguration):
    __slots__ = ()

    @classmethod
    @validator_backup
    def _make_schema(cls):
        """Create a schema and return the collector that contains it"""
        collector = KeyValueStoreSchemaValidator()
        ValidatedKeyValueStoreSchema.set_validator(collector)

        ValidatedKeyValueStoreSchema('section', dict(
            string='somevalue',
            int=40,
            float=5.0,
            list=['a', 'b', 'c'],
            subsection=dict(
                string='oval',
                list=[0]
            )
        )
        )

        ValidatedKeyValueStoreSchema(RootKey, dict(some_option='value'))
        return collector
        # end create test schemas with own collector

    @classmethod
    @validator_backup
    def _make_configuration_schema(cls):
        """Setup a collector which represent our test configuration"""
        collector = KeyValueStoreSchemaValidator()
        ValidatedKeyValueStoreSchema.set_validator(collector)

        ValidatedKeyValueStoreSchema('db.ldap', dict(server_url='ldap://nowhere'))
        ValidatedKeyValueStoreSchema('db.meta', dict(server_url='metadb://somewhere'))
        ValidatedKeyValueStoreSchema('host', dict(path_separator='/'))
        ValidatedKeyValueStoreSchema('maya', dict(quality_check_gui=dict(may_ignore_check=False)))
        ValidatedKeyValueStoreSchema('paths.cache_root', dict(fs_path='There'))
        ValidatedKeyValueStoreSchema('paths.project_root', dict(fs_path='over_here'))
        ValidatedKeyValueStoreSchema('platform', dict(path_separator='/'))
        ValidatedKeyValueStoreSchema('quality_check_gui', dict(do_it_right=True))
        ValidatedKeyValueStoreSchema('site', dict(location='munich_schwabing',
                                                  name='klenze7_munich'))
        return collector

    def test_schema_validation(self):
        """assure a config schema can be validated"""
        validator = self._make_schema()

        # the default schema is correct
        _, clashes = validator.validate_schema()
        assert len(clashes) == 0, "Did expect a valid schema"

        # if we duplicate a value, it would clash, but won't as the value is the same !
        validator.append(ValidatedKeyValueStoreSchema(RootKey, dict(some_option='value'),  validator=validator))
        last_schema = validator[-1]
        _, clashes = validator.validate_schema()
        assert len(clashes) == 0, "Didnt expect clash for similar values"

        # if there is an actual change, there it will be detected
        clashing_key = 'some_option'
        last_schema[clashing_key] = 'different_value'
        _, clashes = validator.validate_schema()
        assert len(clashes) == 1 and clashes[0] == clashing_key

    def test_provider_validation(self):
        """assure config providers can be validated"""
        cmod = YAMLKeyValueStoreModifier(test_serialize.TestYamlConfiguration.config_fixtures(('lnx', 'maya')))
        collector = self._make_configuration_schema()

        assert len(collector.validate_schema()[-1]) == 0, "Schema schould be correct"

        # its invalid to have missing values in the configuration, or an unconvertible type
        cmod.delete_value('quality_check_gui')
        collector[-1].location = 40        # cannot convert 'munich' to int

        issue_index = collector.validate_provider(cmod)
        assert len(issue_index) == 2, "Should have two issues"

        # Simple test to see how the schema can be used to safely access values
        qc_gui_schema = collector[-2]
        assert cmod.value(qc_gui_schema.key(), qc_gui_schema).do_it_right == True


# end class TestSchema
