#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_components
@brief Tests our component implementations

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from butility.tests import TestCaseBase
from bapp.tests import with_application
from bprocess import ( ProcessControlContextControllerBase,
                       ProcessConfigurationIncompatibleError )
from bkvstore import YAMLKeyValueStoreModifier


class TestProcessController(ProcessControlContextControllerBase):
    __slots__ = ()

    def _setup_scene_callbacks(self):
        """noop"""
        pass
# end class TestProcessController


class TestProcessControlContextController(TestCaseBase):
    """Verify the context controller, triggering a few of its functions manually"""
   
    @with_application
    def test_base(self):
       """verify basic functionality"""
       ctrl = TestProcessController()
       ctrl.set_static_stack_len()
       
       assert len(ctrl.pop_asset_context()) == 0, 'should have popped nothing, but its okay'
       
       kv_a = YAMLKeyValueStoreModifier([self.fixture_path('processcontrol/process_config_a.yaml')])
       kv_a_changed_version = YAMLKeyValueStoreModifier([self.fixture_path('processcontrol/process_config_a_changed_version.yaml')])
       kv_a_changed_requires = YAMLKeyValueStoreModifier([self.fixture_path('processcontrol/process_config_a_changed_requires.yaml')])
       
       # this shouldn't raise anything
       ctrl._check_process_compatibility(kv_a, kv_a, program = 'foo')
       
       self.failUnlessRaises(ProcessConfigurationIncompatibleError, ctrl._check_process_compatibility, kv_a_changed_version, kv_a, 'foo')
       self.failUnlessRaises(ProcessConfigurationIncompatibleError, ctrl._check_process_compatibility, kv_a_changed_requires, kv_a, 'foo')
       
       
   
# end class TestProcessControlContextController

