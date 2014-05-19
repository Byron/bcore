#-*-coding:utf-8-*-
"""
@package bqc
@brief a module containing base classes for the quality check framework

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""

__all__ = [ 'QualityCheckCategory', 'NoCategory', 'QualityCheck', 'QualityCheckRunner', 
            'QualityCheckRunnerDelegate', 'StreamingQualityCheckRunnerDelegate']

import sys
import traceback
import logging

from butility import ( abstractmethod,
                      Interface,
                      wraps )

from .interfaces import ( IQualityCheck,
                          IQualityCheckRunner,
                          IQualityCheckRunnerDelegate,
                          QualityCheckCategory )


# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

## @note looks like this could be done with properties as well
## @note also, from the name of this decorator it's not apparent that the value can't be None
##       that would be better handled by not hasattr -> raise error, value is None -> return value
##       and a seperate not_none decorator

def return_member(name):
    """A decorator returning a member with `name` of the input instance
    @note raise if the member does not exist or is None"""
    def function_receiver(fun):
        """receives the actual function to wrap"""
        @wraps(fun)
        def wrapper(instance):
            """implements obtaining the member"""
            try:
                rval = getattr(instance, name)
                if rval is None:
                    raise AttributeError
                return rval
            except AttributeError:
                cls = instance
                if not isinstance(instance, type):
                    cls = type(instance)
                #end obtain class instance
                raise AssertionError("Class %s has to set the %s member" % (cls.__name__, name))
            #end exception handling
        #end wrapper
        return wrapper
    #end function receiver
    return function_receiver

## -- End Decorators -- @}


class NoCategory(QualityCheckCategory):
    """ constant for qualitychecks that don't set their category """
    _name        = 'None'
    _description = ''


class QualityCheckRunnerDelegate(IQualityCheckRunnerDelegate):

    __slots__ = tuple()
    
    log = logging.getLogger('bqc.base.QualityCheckRunnerDelegate')
    
    # -------------------------
    ## @name Interface
    # @{
    
    def handle_error(self, quality_check):
        """@note the base implementation will just log the exception, but will not raise"""
        self.log.error("Exception occurred when running or fixing quality check '%s'", 
                                                                    quality_check.name(), exc_info=True)
    
    def post_fix(self, quality_check):
        assert isinstance(quality_check, QualityCheck)
        if quality_check.result() != quality_check.success:
            quality_check.reset_result().run()
        #end handle check state
        
    ## -- End Interface -- @}


class QualityCheck(IQualityCheck):
    """A base class providing the foundation for all actual QualityCheck implementations."""
    __slots__ = (
        '_result',   # result constant of the last run
        )
    
    # -------------------------
    ## @name Categories
    # @{
    
    ## Indicates that this instance is not in any category
    no_category = NoCategory
    
    ## -- End Categories -- @}

    # -------------------------
    ## @name Constants
    # @{
    
    success = 'success'
    failure = 'failure'
    no_result = 'no_result'
    
    result_constants = (success, failure, no_result)
    
    ## -- Constants -- @}
    
    # -------------------------
    ## @name Subclass Configuration
    # Subclasses should override these members with the values they prefer
    # For more information see the respective class method below. 
    # @{
    
    ## mandatory, see `name()`
    _name = None
    ## mandatory, see `description()`
    _description = None
    ## see `category()`
    _category = no_category
    ## see `can_fix()`   
    _can_fix = False

    ## -- Subclass Configuration -- @}
     
    def __init__(self):
        """Initialize this base
        @attention needs to be called by sub-class"""
        self.reset_result()
    
    ## @name Interface
    # -------------------------
    # @{
    
    @abstractmethod
    def run(self):
        """ @return this instance, which should be used to obtain the result by calling the `result()` method.
        @attention implementations must set the `_result` member of this instance to the respective result constant.
        """
        return self
        
    def result(self):
        """@returns the result of the previous `run()` call, which may be `success` or `failure`. 
        If the check didn't yet run, it is `no_result`.
        """
        return self._result
        
    def reset_result(self):
        """Reset the result of the previous run
        @return this instance"""
        self._result = QualityCheck.no_result
        return self
        
    def fix(self):
        """@returns this instance to facilitate re-checking the issue. If it is truly fixed, the check should 
        confirm this.
        @note `result()` might still be `failure` as the check might not be certain it succeeded until it is
        being re-run.
        @throw any exception is possible in case the implementation has encountered an unforeseen situation.
        Callers should protect against it.
        @attention derived types must call their superclass at the **end** of their implementation and return 
        its value as it will  perform some sanity checks.
        The result will remain failed (unless the sub-class is sure it fixed the issue and sets the result) so
        that the check would have to be re-run to verify it"""
        assert self.can_fix(), "Cannot call superclass' fix() method if can_fix returns False"
        return self
        
    def can_fix(self):
        """@returns true if the implementation supports fixing of the detected issue
        @note this state can be dependent on the actual run, therefore it should be validated right before
        trying to call the `fix()` method.
        """
        return self._can_fix
    
    ## -- Interface -- @}
    
    # -------------------------
    ## @name Information
    # methods to provide static information about this check
    # @{
    
    @classmethod
    def uid(cls):
        """@returns a hashable id which is unique for this type of check.
        @note you could use it as a key to attach additional data with items of this type
        """
        return cls.__name__
    
    @classmethod
    @return_member('_name')
    def name(cls):
        """@returns the name of the check, as suitable for UI purposes."""
    
    @classmethod
    @return_member('_description')
    def description(cls):
        """@returns the detailed description of the check, which includes information about
        - **what the check is looking for**
        - **the problems common causes**
        - **solutions for the problem** in case it doesn't implement a fix.
        """
    
    @classmethod
    @return_member('_category')
    def category(cls):
        """@returns an instance of `QualityCheckCategory` which serves as group. The same instance is used by multiple
        quality checks.
        
        Can be the special constant `QualityCheck.no_category`, which is the default.
        """

    ## -- Information -- @}
# end class QualityCheck    


class QualityCheckRunner(IQualityCheckRunner):
    """Is a list of `QualityCheck` compatible instances which can be run safely, providing just-in-time information
    about the results of this run.
    
    For this, it uses a delegate which will receive respective calls. The client can implement one, but even 
    without a default delegate is used which does nothing
    """
    __slots__ = (
                '_delegate'
                )
    
    # -------------------------
    ## @name Constants
    # @{
    
    ## indicates the check should be skipped
    skip_check = 'skip_check'
    
    ## indicates that the current quality check run should be stopped entirely
    stop_run = 'stop_run'
    
    ## default logger we will use
    log = logging.getLogger('bqc.base.QualityCheckRunnerDelegate')
    
    ## -- End Configuration -- @}
    
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## the delegate to be created if there is no explicit delegate type
    DefaultDelegateType = QualityCheckRunnerDelegate
    
    ## -- End Configuration -- @}

    def __init__(self, quality_checks, delegate=None):
        super(IQualityCheckRunner, self).__init__(quality_checks)
        if delegate is None:
            self._delegate = self.DefaultDelegateType()
        else:
            self._delegate = delegate
        #end handle delegate initialization
        
    def run_one(self, quality_check, auto_fix=False):
        assert isinstance(quality_check, QualityCheck)
        # PRE RUN
        #########
        dres = self._delegate.pre_run(quality_check)
        if dres is self.skip_check:
            return quality_check
        #end handle skip checks
        if dres is self.stop_run:
            raise StopIteration()
        #end handle stop iteration
        
        # RUN
        #######
        fix_threw_exception = False
        try:
            res = quality_check.reset_result().run().result()
            if res == quality_check.no_result:
                msg =  "Quality check %s should have set the result of the run" % type(quality_check).__name__
                raise AssertionError(msg)
            #end assertion
            
            if auto_fix and res == quality_check.failure and quality_check.can_fix():
                try:
                    self._delegate.pre_fix(quality_check)
                    quality_check.fix()
                    self._delegate.post_fix(quality_check)
                except Exception:
                    # keep this info as delegate might re-raise, and we don't want to catch it again 
                    fix_threw_exception = True
                    self._delegate.handle_error(quality_check)
                #end log unexpected errors
            #end attempt to fix the problem
        except Exception:
            if not fix_threw_exception:
                self._delegate.handle_error(quality_check)
            else:
                # re-raise an exception that the delegate has thrown 
                raise
            #end prevent duplicate error handling
        #end handle qc exception
        
        # POST RUN
        ##########
        dres = self._delegate.post_run(quality_check)
        if dres is self.stop_run:
            raise StopIteration()
        #end handle stop iteration
        return quality_check
        
    def run_all(self, auto_fix=False):
        for qci in self:
            try:
                self.run_one(qci, auto_fix=auto_fix)
            except StopIteration:
                break
            #end handle stop iteration
        #end for each quality check instance
        return self
        
    def delegate(self):
        return self._delegate
        
# end class QualityCheckRunner

# ==============================================================================
## @name Delegates
# ------------------------------------------------------------------------------
# Implementations for various quality check delegates
## @{

class StreamingQualityCheckRunnerDelegate(QualityCheckRunnerDelegate):
    """A delegate that writes information about the runner's progress to streams
    
    @note we do not explicitly flush streams after writing
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    # stream object to be used for ordinary output, which is triggered by anything done by the checks
    output = sys.stdout
    
    # stream object used to signal actual implementation errors
    error = sys.stderr
    
    ## -- End Configuration -- @}
    
    def _check_failed(self, check):
        """@return True if the check failed"""
        assert isinstance(check, QualityCheck)
        return check.result() != check.success
    
    def handle_error(self, quality_check):
        """Write traceback and info"""
        self.error.write(traceback.format_exc() + "\n")
        self.error.write("Unhandled exception caught for quality check '%s'\n" % quality_check.name())
    
    def pre_run(self, quality_check):
        """write short info"""
        self.output.write("%s ... " % quality_check.name())
        
    def post_run(self, quality_check):
        """Print info about failure or success"""
        suffix = "OK"
        if self._check_failed(quality_check):
            suffix = "FAILED"
        #end
        
        self.output.write("%s\n" % suffix)
        if self._check_failed(quality_check):
            # write description, indented
            for line in quality_check.description().split('\n'):
                self.output.write("\t%s\n" % line)
            #end for each line
        #end print extended description
        
    def post_fix(self, quality_check):
        """re-run the check and see if it was truly fixed"""
        # runs it again ... 
        super(StreamingQualityCheckRunnerDelegate, self).post_fix(quality_check)
        if not self._check_failed(quality_check):
            self.output.write("(FIXED) ")
        #end print info about it being fixed
        
        
# end class StreamingQualityCheckRunnerDelegate

## -- End Delegates -- @}


