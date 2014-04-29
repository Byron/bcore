#-*-coding:utf-8-*-
"""
@package bapp.tests.processing.transaction.test_transaction
@brief tests for btransaction

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import time
import logging

from butility.tests import TestCaseBase
from butility import ConcurrentRun

from btransaction import *

log = logging.getLogger('btransaction.tests.test_transaction')

#{ Utiltiies

class TestOp(Operation):
	def __init__(self, transaction):
		super(TestOp, self).__init__(transaction)
		self._value = 0


class FailOp(TestOp):
	name = "FailOp"
	description = "Op that fails"
	
	def apply(self):
		self._value += 1
		assert self._progress() is not None
		assert not self._dry_run()
		raise Exception("Failed on operation")
		self._value += 1	# never runs, obviously
		
	def rollback(self):
		assert self._progress() is not None
		assert self._value == 1
		self._value -= 1


class SuccessOp(TestOp):
	name = "SuccessOp"
	description = "Op that succeeds"
	
	
	def apply(self):
		self._value += 2
		
	def rollback(self):
		assert self._value == 2
		self._value -= 2
		

class LongRunningOp(TestOp):
	name = "LongrunningOp"
	description = "Op that taks a lnog time"
	
	def apply(self):
		while self._value < 1000:
			self._abort_point()
			self.log.info("incrementing value")
			self._value += 1
			time.sleep(0.001)
		#END while we have work to do
		
	def rollback(self):
		"""Rollback is fast"""
		while self._value != 0:
			assert not self._should_abort()
			self._value -= 1
		#END rollback explicitly

#}END utilities


class TestTransaction(TestCaseBase):
	def test_base(self):
		t = Transaction(log)
		assert t.succeeded() == False, "Should be unsuccessful if it didn't run yet"
		assert not t.is_done(), "Should not yet be done"
		assert t.exception() is None, "There should be no exception if it didn't run"
		assert not t.is_aborting(), "It shouldn't yet abort"
		assert t.progress() is None, "Should have no progress while its not running"
		assert not t.is_running(), "shouldn't be running after instantiation"
		assert not t.is_rolling_back(), "Shouldn't be rolling back after init"
		assert not t.rollback().succeeded(), "Cannot rollback without having performed the operation"
		assert not t.aborted(), "Shouldn't be aborted in a plain vanilla transaction"
		
		
		# successful operation
		######################
		so = SuccessOp(t)
		so2 = SuccessOp(t)
		
		assert t.apply().succeeded(), "Transaction should be successfull after it ran"
		assert t.is_done(), "transaction should be done now"
		assert t.exception() is None
		assert so._value == 2
		assert so2._value == 2
		assert t.progress() is None, "no progress after transaction"
		assert t.is_running() == False, "its not running anymore"
		
		assert t.apply().succeeded(), "Transaction doesn't actually run multiple times"
		assert so._value == 2  and so2._value == 2
		
		# Rollback
		##########
		assert not t.rollback().succeeded(), "After rollback its like nothing happened"
		assert so._value == 0 and so2._value == 0, "Rollback should have been called on operation"
		assert not t.is_running() and t.progress() is None, "Shouldn't be running anymore"
		
		# can re-apply
		assert t.apply().succeeded(), "Should be successful after apply"
		assert so._value == 2, "operation should have been called"
		
		# Failling operation
		####################
		t = Transaction(log)
		so = SuccessOp(t)
		fo = FailOp(t)
		
		assert not t.apply().succeeded(), "Transaction should fail this time"
		assert so._value == 0 and fo._value == 0
		assert isinstance(t.exception(), Exception), "exception was expected"
		
		assert not t.rollback().succeeded(), "Rollback should not work without apply()"
		assert not t.apply().succeeded(), "apply() should fail in second run as well"
		assert so._value == 0
		
		# Abort long-running operations
		################################
		t.clear()
		lo = LongRunningOp(t)
		cr = ConcurrentRun(t.apply, t.log).start()
		time.sleep(0.002)
		assert t.is_running(), "Should be runnning now"
		assert t.progress() is not None, "When running, there is a progress"
		assert lo._value > 0, "Should have managed to do some work after waiting"
		assert not t.is_aborting()
		assert t.abort(True).is_aborting(), "Should be aborting after setting the state - if this fails its an async issue"
		assert cr.result() is t, "Wait for transaction yielded unexpected result"
		assert lo._value == 0, "Rollback should have occurred"
		assert not t.succeeded(), "op shold not have been successful after abort"
		assert not t.is_rolling_back(), "Shouldn't be rolling back once we are done with it"
	
