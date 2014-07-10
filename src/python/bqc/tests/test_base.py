#-*-coding:utf-8-*-
"""
@package bapp.tests.qc.test_base
@brief tests for bqc.base

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = []

import bapp
from butility.tests import TestCase
from bqc import *

from butility.compat import StringIO

# ==============================================================================
## @name TestTypes
# ------------------------------------------------------------------------------
## @{

class TestStreamingDelegate(StreamingQualityCheckRunnerDelegate):
    """Overrides streams"""
    __slots__ = ()
    
    output = StringIO()
    error = StringIO() 

# end class TestStreamingDelegate



## -- End TestTypes -- @}




# ==============================================================================
## @name Testing Mockups
# ------------------------------------------------------------------------------
## @{

class QualityCheckMockup(QualityCheck, bapp.plugin_type()):
    """A utility to test the quality check framework """

    __slots__ = (
                    '_fixed',        # if true, we consider the issue fixed
                    '_raise_at_runtime' # if True, an exception will be raised at runtime
                )
    
    _name = "name"
    _description = "description"
   
    def __init__(self):
        super(QualityCheckMockup, self).__init__()
        self._fixed = None
        self._raise_at_runtime = False

    def run(self):
        """run the `check_target_quality` method and verify if the target satisfies check conditions
        Returns failure by default."""
        if self._raise_at_runtime:
            raise TypeError("Controlled exception")
        #end raise at runtime
        if self._fixed is not None:
            self._result = self._fixed and QualityCheck.success or QualityCheck.failure
        else:
            self._result = QualityCheck.failure
        #end handle result according to fixed state
        return self
    
    def fix(self):
        """if `can_fix()` runs the fix and set _fixed to True otherwise to False"""
        self._fixed = True
        return super(QualityCheckMockup, self).fix()
        
    def can_fix(self):
        return self._fixed is not None and True or False
        
    # -------------------------
    ## @name Test Interface
    # @{
    
    def set_unfixed(self):
        """Set the issue to be unfixed"""
        self._fixed = False
        return self
            
    def set_result(self, result):
        """set this instance to use the given result"""
        self._result = result
        
    def set_raises(self, state):
        """Make this instance raise during run"""
        self._raise_at_runtime = state
        
        
    ## -- End Test Interface -- @}


class QualityCheckRunnerDelegateMockup(QualityCheckRunnerDelegate, bapp.plugin_type()):
    """Implements a simple delegate for testing purposes, to help assuring the runner works within its bounds."""
    __slots__ = (
                    # user configuration
                    'pre_run_result',       # returned during pre-run
                    'post_run_result',      # returned during post-run
                    
                    # read-only information about the run
                    'exception_encountered',# is True if the check encountered an exception
                    'fix_attempted',        # is True if we entered the pre_fix() method
                )
    
    def __init__(self):
        super(QualityCheckRunnerDelegateMockup, self).__init__()
        self.pre_run_result = None
        self.post_run_result = None
        self.reset()
        
    def reset(self):
        """Reset all state, except for our configuration"""
        self.exception_encountered = False
        self.fix_attempted = False
    
    def pre_run(self, quality_check):
        """performs according to our configuration"""
        return self.pre_run_result
        
    def handle_error(self, quality_check):
        """just remember the exception"""
        self.exception_encountered = True
        
    def post_run(self, quality_check):
        """performs according to our configuration"""
        return self.post_run_result
        
    def pre_fix(self, quality_check):
        """ """
        self.fix_attempted = True

# end class QualityCheckRunnerDelegateMockup
            
## -- End Testing Mockups -- @}


class TestQualityCheckFramework(TestCase):
    
    def test_class_methods(self):
        """Verify class interface of quality check"""
        qcm = QualityCheckMockup
        self.failUnless(qcm.name() == qcm._name)
        assert qcm.description() == qcm._description
        assert qcm.category() is QualityCheck.no_category
        assert hash(qcm.uid()) == hash(qcm.uid()), "UID should be hashable and deterministic"
        
    def test_category(self):
        """check category access"""
        name = 'name'
        desc = 'desc'
        class TestQualityCheckCategory(QualityCheckCategory):
            _name        = name
            _description = desc
        
        cat = TestQualityCheckCategory
        
        self.failUnless(cat.name() == name)
        assert cat.description() == desc

        cat2 = TestQualityCheckCategory
        
        assert cat == cat2
        
    def test_quality_check(self):
        """Testing the quality check mockup"""
        qci = QualityCheckMockup()
        assert qci.result() is QualityCheck.no_result, "Shouldn't have any result yet"
        assert not qci.can_fix()
        self.failUnless(qci.run().result() is QualityCheck.failure)
        assert qci.reset_result().result() is QualityCheck.no_result
        
        assert qci.set_unfixed().can_fix()
        assert qci.run().result() is QualityCheck.failure
        assert qci.fix().run().result() is QualityCheck.success
        
    def test_runner(self):
        """verify runner operation"""
        qck = QualityCheckMockup()
        dlg = QualityCheckRunnerDelegateMockup()
        qcr = QualityCheckRunner((qck, ), delegate=dlg)
        # have exactly one item
        assert len(qcr) == 1
        
        assert qcr.delegate() is dlg
        
        assert qck.result() == QualityCheck.no_result, "precondition: check is not yet done"
        dlg.pre_run_result = qcr.skip_check
        assert qcr.run_one(qck).result() is QualityCheck.no_result, "Expected the check to be skipped"
        assert dlg.exception_encountered == False
        
        dlg.pre_run_result = None
        assert qcr.run_all()[0].result() is QualityCheck.failure
        
        # verify it can handle exceptions
        dlg.reset()
        qck.set_raises(True)
        qcr.run_all()
        assert dlg.exception_encountered, "Should have been receiving an exception on a failed run"
        assert not dlg.fix_attempted, "Shouldn't have tried a fix by default"
        dlg.reset()
        
        # verify stop-run stops the iteration
        dlg.post_run_result = qcr.stop_run
        self.failUnlessRaises(StopIteration, qcr.run_one, qck)
        dlg.post_run_result = None
        dlg.reset()
        
        # verify the check is being fixed
        qck.set_raises(False)
        qck.set_unfixed()
        assert not dlg.fix_attempted
        assert qcr.run_all(auto_fix=True) is qcr
        assert dlg.fix_attempted
        assert qcr[0].result() is QualityCheck.success, "Expected success when item was fixed"
        dlg.reset()
        
    def test_stream_delegate(self):
        """Verify the stream delegate works"""
        qck = QualityCheckMockup()
        dlg = TestStreamingDelegate()
        qcr = QualityCheckRunner((qck, ), delegate=dlg)
        
        # for now, just let it run in a few modes - we don't really analyse it
        qck.set_unfixed()
        qcr.run_all(auto_fix=True)
        qck.set_raises(True)
        qcr.run_all()
        qck.set_raises(False)
        qcr.run_all()
        
        self.failUnless(dlg.output.getvalue())
        assert dlg.error.getvalue()
        
# end class TestQualityCheck
    


