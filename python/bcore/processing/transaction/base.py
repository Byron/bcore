#-*-coding:utf-8-*-
"""
@package tx.processing.transaction.base
@brief Module to keep all the basic implementations to handle transactions.

A transaction consists of zero or more Operations, each of which can be rolled back
if an error occours. Operations will be recorded and if required, rolled back in reverse
order.

@copyright 2013 Sebastian Thiel
"""
__all__ = ['Transaction', 'Operation', 'StoringProgressIndicator']

import bcore
from bcore.path import make_path
from bcore import InterfaceBase
from bcore.utility import ProgressIndicator

import weakref
import logging
import threading
import time

TRACE = logging.TRACE


#{ Exceptions

class AbortedExplicitly(Exception):
	"""Exception to indictate that an operation should be aborted"""
	

class LockError(Exception):
	"""Indicate that a lock could not be obtained"""
	
#} END exceptions


class StoringProgressIndicator(ProgressIndicator):
	"""A simple progress instance that stores the message it gets and may append
	some additional progress information to it.
	
	The final progress message may be queried using the message() method"""
	__slots__ = "_message"
	
	def __init__(self, *args, **kwargs):
		super(StoringProgressIndicator, self).__init__(*args, **kwargs)
		self._message = ''
		
	#{ Baseclass Overrides
	def refresh( self, message = None ):
		if message is None:
			message = ''
		else:
			self._message = message
		#END handle message reset
		
	def begin(self):
		super(StoringProgressIndicator, self).begin()
		self._message = ''
	
	def end(self):
		super(StoringProgressIndicator, self).end()
		self._message = ''
		
	#} END base class overrides
		
	#{ Interface
	
	def message(self):
		"""@return the message set on the previous progress. May be empty string
			if the progress was never set or is done"""
		return self._message
	
	#}END interface


class IOperation(InterfaceBase):
	"""Define the simple interface to do and undo operations"""
	
	#{ Interface
	
	@tx.abstractmethod
	def apply(self):
		"""Perform the operation. Keep state to be able to undo the operation at any time
		@return this instance"""
		
	@tx.abstractmethod
	def rollback(self):
		"""Undo the operation you previously performed. Use your state to do that,
		and roll it back as well to allow an apply() call to be potentially successful afterwards.
		
		In case you do not have an internal state to rely on, you have to verify any step you perform
		to be sure you roll back the right thing.
		@return this instance."""
	
	#}END interface


class Transaction(IOperation):
	"""A transaction which keeps a list of operations.
	If you are interested in implementing your own multi-operation transaction, just
	derive from this type and add operations yourself, piggy-bagging on the rollback implementation.
	
	A transaction is meant to run asynchronously , hence you may query what is currently going on, asking 
	for the progress().
	
	The progress is None if the operation is not currently running.
	
	A Transaction can be in dry-run mode, in which case no operation will really do anything.
	However, operations will simulate the operation as good as possible,  and fail if preconditions are not met.
	"""
	# NOTE: Can't really use slots as to not constrain subtypes too much.
	# Slots are good, but it's also too annoying to deal with this multi-inheritance issue that arises from them
	_slots_ = (		"log",
					"_operations",
				 	"_exception", 
				 	"_performed_operation", 
					"_abort_transaction", 
					"_progress_prototype", 
					"_progress", 
					"_dry_run"
					"_lock", 
					"_is_rolling_back")
	
	#{ Configruation
	
	## The name of your transaction. Ideally this is overridden to have a unique 
	## id for a specific type of transaction
	name = "Transaction"

	#END configuration
	
	def __init__(self, log = None, progress = None, dry_run = False):
		self.log = log or service(tx.ILog).new(self.name)
		self._progress_prototype = progress and progress or StoringProgressIndicator()
		self._exception = None
		self._dry_run = dry_run
		self._lock = threading.Lock()
		self.clear()
		
	def _reset_state(self):
		self._performed_operation = False
		self._is_rolling_back = False
		self._progress = None
		self._abort_transaction = False
		
	def _perform_rollback(self, last_op_index):
		"""undo the previous operation, return self
		@param last_op_index index of the last operation which was fully or partly
			performed. This will be the first operation to be undone"""
		# we never actually rollback in dry-run mode
		# we may fail if the rollback fails as well ... this would be calle bug then
		if not self._dry_run:
			self._abort_transaction = False	# make sure noone tries to abort during rollback
			try:
				self.log.log(TRACE, "%s: Commencing rollback" % self.name)
				self._progress = self._progress_prototype
				self._progress.begin()
				self._is_rolling_back = True
				try:
					for op_index in range(last_op_index, -1, -1):
						op = self._operations[op_index]
						self.log.log(TRACE, "%s->%s: %s commencing rollback ... " % (self.name, op.name, op.description))
						op.rollback()
						self.log.log(TRACE, "%s->%s: %s rollback done" % (self.name, op.name, op.description))
					#END for each op
				finally:
					self._is_rolling_back = False
					self._progress.end()
					self._progress = None
				#END handle state
				self.log.log(TRACE, "%s: rollback done" % self.name)
			except Exception:
				self.log.critical("%s->%s: Unhandled exception during rollback", self.name, op.name, exc_info=True)
				raise
			# END exception handling
		#END ignore rollback in dry-run
		self._reset_state()	# we are all good now
		return self

	def __iter__(self):
	    """@return an iterator on our operations. For inspection only !"""
	    return iter(self._operations)
		
	#{ Operations Interface
	
	def _add_operation(self, operation):
		# lets just assume this is not a performance issue for now.
		assert operation not in self._operations, "Operation was already part of transaction"
		self._operations.append(operation)
		
	def _abort_point(self):
		"""called by Operations to trigger an exception if the user requested to abort.
		In that case, an exception will be thrown.
		This may be set asynchronously"""
		if self._should_abort():
			raise AbortedExplicitly("Operation aborted by User")
		#END
		
	def _should_abort(self):
		"""@return true if the operation should abort"""
		return self._abort_transaction
		
	#} END operations interface
	
	#{ Interface
	
	def succeeded(self):
		"""@return true if the previous call to apply() was successful, False otherwise or if apply() 
		did not yet run"""
		if not self._performed_operation:
			return False
		return not self.failed()
		
	def wait(self, recheck_every = 0.05, wakeup_call = None):
		"""Wait for the transaction to be done, recheck evrey given amount of seconds.
		When woken up, call given wakeup_call() if not None
		@return self"""
		while self.is_running():
			time.sleep(recheck_every)
			if wakeup_call is not None:
				wakeup_call()
			#END call custom code
		#END wait loop
		return self
		
	def failed(self):
		"""@return True if this instance failed. Call exception() to obtain more information
		about the cause of the issue"""
		return self._exception is not None
		
	def is_done(self):
		"""@return true if the operation was applied successfully. Please note that this will never
		be true if apply() failed. False is returned if a rollback was performed also"""
		return self._performed_operation
		
	def is_rolling_back(self):
		"""@return True if we are currently rolling back the transaction"""
		return self._is_rolling_back
		
	def exception(self):
		"""@return exception in case the previous apply() call was not successful. 
		Will be reset on next apply()"""
		return self._exception
		
	def abort(self, state):
		"""Set this transaction to abort as soon as possible if state is True
		@return self"""
		if self._is_rolling_back:
			return self
		# end while rolling back, we can't abort
		self._abort_transaction = state
		return self
		
	def is_aborting(self):
		"""@return True if the transaction is supposed to abort"""
		return self._should_abort()
		
	def aborted(self):
		"""@return True if the operation was aborted"""
		return isinstance(self.exception(), AbortedExplicitly)
		
	def is_running(self):
		"""@return true if we are currently executing the transaction, which is either apply()
		or rollback()"""
		rval = self._lock.acquire(False)
		if rval:
			self._lock.release()
		return rval == False
		
	def progress(self):
		"""@return an ProgressIndicator instance that can be used to obtain progress information
		or None if is_running() is False"""
		if not self.is_running():
			return None
		return self._progress
		
	def is_dry_run(self):
		"""@return True if the transaction is in dry-run mode, and will thus not really do anything"""
		return self._dry_run
		
	def clear(self):
		"""Remove all operations and reset the state. This allows the instance to be reused
		@note may block if an apply operation is in progress"""
		self._lock.acquire()
		try:
			self._reset_state()
			self._operations = list()
		finally:
			self._lock.release()
		#END handle lock
		
	#} END interface
	
	
	#{ Interface Implementation
	
	def apply(self):
		"""Apply all operations stored so far but roll them back if one fails
		This method is thread-safe."""
		self._lock.acquire()
		try:
			if self._performed_operation:
				return self
			#END prevent duplicate execution
			try:
				self._exception = None
				self._progress = self._progress_prototype
				self._progress.begin()
				try:
					self.log.log(TRACE, "'%s' transaction starting ..." % self.name)
					for op_index, op in enumerate(self._operations):
						self._abort_point()
						self.log.log(TRACE, "%s->%s: %s starting ... " % (self.name, op.name, op.description))
						op.apply()
						self.log.log(TRACE, "%s->%s: done" % (self.name, op.name))
						self._abort_point()
					#END for each op
				finally:
					self._progress.end()
				#END assure to reset progress
				# only clear progress once we are successful 
				# we don't want 'holes' as we will roll back in a short moment
				self._progress = None
				self.log.log(TRACE, "'%s' transaction done" % self.name)
			except Exception, e:
				if isinstance(e, AbortedExplicitly):
					# show where it was aborted, just for further info
					self.log.warn("%s->%s: operation aborted", self.name, op.name, exc_info=True)
				else:
					self.log.error("%s->%s: An unhandled exception occurred", self.name, op.name, exc_info=True)
				#END handle logging
				self._perform_rollback(op_index)
				
				# set us failed AFTER the rollback was performed
				self._exception = e
				return self
			#END handle errors
			self._performed_operation = True
		finally:
			self._lock.release()
		#END assure lock release
		
		return self
		
	def rollback(self):
		"""The previous operation, will only do something if it was successful"""
		if not self._performed_operation:
			return self
		
		self._lock.acquire()
		try:
			return self._perform_rollback(len(self._operations) - 1)
		finally:
			self._lock.release()
			
		#END assure lock release
	
	#}END interface implementation
	
	
class Operation(IOperation):
	"""A single operation which can be undone on error. It may only be part of
	a single transaction at all times.
	
	Derive from this instance and implement the apply() and rollback() methods. You should
	keep track of your state as required to be able to undo an operation.
	
	Once an undo was performed, you should be in a state which allows you to apply()
	once again.
	
	Durning apply(), call _abort_point() to abort if the user requested this.
	During apply() and rollback(), you may use the _progress() instance to provide
	additional information about your current progress.
	
	If you notice that your operation is already performed, so you don't have to 
	do anything, you should gently do nothing and return without failure
	
	Check your _dry_run() flag during apply(), and in case its true, don't really
	perform your actual operation.
	"""
	__slots__ = (
					"_transaction", 
					"log"
				)
	
	#{ Configuration
	
	# A descriptive name for your operation
	name = "Operation"
	
	# A description of the operation 
	description = "performs something"
	
	#} END configuration
	
	def __init__(self, transaction, log = None):
		"""Initialize this instance as part of the given transaction
		If log is not set, we will initialize our logger from the parents logger"""
		self._transaction = weakref.ref(transaction)
		self.log = log or service(tx.ILog).new(self._transaction().log.name + '.' + self.name)
		transaction._add_operation(self)
		
	#{ Subclass Interface
	
	def _should_abort(self):
		"""@return true if we should abort"""
		return self._transaction()._should_abort()
		
	def _abort_point(self):
		"""Raise an exception if we should abort. Call it during your operation
		in order to make it more responsive. To the users's abort calls."""
		self._transaction()._abort_point()
		
	def _progress(self):
		"""@return ProgressIndicator instance allowing to set the progress of this operation"""
		return self._transaction().progress()
		
	def _dry_run(self):
		return self._transaction().is_dry_run()
		
	#}END subclass interface
