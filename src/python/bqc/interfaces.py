#-*-coding:utf-8-*-
"""
@package bqc.interfaces
@brief Interfaces used in the quality checking framework

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from future.builtins import object
__all__ = ['IQualityCheck', 'IQualityCheckProvider', 'IQualityCheckRunnerDelegate', 'IQualityCheckRunner', 
            'QualityCheckCategory']

from butility import ( abstractmethod,
                       Interface )

# -------------------------
## @name Utility
# @{

class QualityCheckCategory(object):
    """ Serves as group for `QualityCheck` implementations, and provides additional static information """   
    
    # -------------------------
    ## @name Subclass Overrides
    # @{
    
    _name = None
    _description = None
    
    ## -- End Subclass Overrides -- @}

    def __init__(self, name, description):
        self._name = name
        self._description = description

    @classmethod
    def name(cls):
        """ @returns the gui friendly name of the category """
        return cls._name
        
    @classmethod
    def description(cls):
        """ @returns a descriptive text further describing the anticipated contents of the category """
        return cls._description
        
# end class QualityCheckCategory

## -- End Utility -- @}


class IQualityCheckProvider(Interface):
    """A simple interface implementing an algorithm to select checks for the current context"""
    __slots__ = ()
    
    @abstractmethod
    def checks(self):
        """@return an iterable of IQualityCheck compatible instances. It is valid for it to yield no quality check"""
        
# end class IQualityCheckProvider


class IQualityCheck(Interface):
    """A base class providing the foundation for all actual QualityCheck implementations."""
    __slots__ = ()      
   
   
    ## @name Interface
    # -------------------------
    # @{
    
    @abstractmethod
    def run(self):
        """ @return this instance, which should be used to obtain the result by calling the `result()` method.
        @attention implementations must set the `_result` member of this instance to the respective result constant.
        """
    
    @abstractmethod    
    def result(self):
        """@returns the result of the previous `run()` call, which may be `success` or `failure`. 
        If the check didn't yet run, it is `no_result`.
        """
    
    @abstractmethod    
    def reset_result(self):
        """Reset the result of the previous run
        @return this instance"""
   
    @abstractmethod    
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
    
    @abstractmethod            
    def can_fix(self):
        """@returns true if the implementation supports fixing of the detected issue
        @note this state can be dependent on the actual run, therefore it should be validated right before
        trying to call the `fix()` method.
        """
    
    ## -- Interface -- @}
    
    # -------------------------
    ## @name Information
    # methods to provide static information about this check
    # @{
    
    @classmethod
    @abstractmethod
    def uid(cls):
        """@returns a hashable id which is unique for this type of check.
        @note you could use it as a key to attach additional data with items of this type
        """
        
    @classmethod
    @abstractmethod
    def name(cls):
        """@returns the name of the check, as suitable for UI purposes."""
    
    @classmethod
    @abstractmethod
    def description(cls):
        """@returns the detailed description of the check, which includes information about
        - **what the check is looking for**
        - **the problems common causes**
        - **solutions for the problem** in case it doesn't implement a fix.
        """
    
    @classmethod
    @abstractmethod
    def category(cls):
        """@returns an instance of `QualityCheckCategory` which serves as group. The same instance is used by multiple
        quality checks.
        
        Can be the special constant `IQualityCheck.no_category`, which is the default.
        """

    ## -- Information -- @}
# end class IQualityCheck    


class IQualityCheckRunner(list, Interface):
    """Is a list of `QualityCheck` compatible instances which can be run safely, providing just-in-time information
    about the results of this run.
    
    For this, it uses a delegate which will receive respective calls. The client can implement one, but even 
    without a default delegate is used which does nothing
    """
    __slots__ = ()
    
    @abstractmethod
    def __init__(self, quality_checks, delegate=None):
        """Initialize this instance with an iterable of quality checks and an (optional) delegate.
        @param quality_checks an iterable of `QualityCheck` subclasses instances. Its contents will be cached
        within the runner
        @param delegate an instance of type `QualityCheckRunnerDelegate`  or None, in which case a default delegate
        will be used.
        """

    @abstractmethod
    def run_one(self, quality_check, auto_fix=False):
        """Run a single quality check
        @param quality_check a quality check instance, it does not necessarily need to be contained in this instance
        @param auto_fix if True, failed checks will attempt to fix the issue if this is implemented by the check.
        @return the result of the quality check instance
        @throw StopIteration if the delegate indicates it wants to stop the entire iteration (in case this call
        is part of an actual iteration)
        @note our delegate will be called accordingly
        """
       
    @abstractmethod
    def run_all(self, auto_fix=False):
        """Safely run all quality check instances contained in this instance and provide progress information 
        to our delegate.
        
        @param auto_fix see `run_one(...)` method for more information
        @return this instance
        """

        for qci in self:
            try:
                self.run_one(qci, auto_fix=auto_fix)
            except StopIteration:
                break
            #end handle stop iteration
        #end for each quality check instance
        return self
        
    @abstractmethod
    def delegate(self):
        """@return our delegate instance"""
        
# end class IQualityCheckRunner


class IQualityCheckRunnerDelegate(Interface):
    """Defines a callback interface to be used by `QualityCheckRunner` instances
    
    The delegate may control the runner by returning codes for the runner to interpret.
    @note the delegate is assumed to perform logging duties if this is required.
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Interface
    # @{
    
    def handle_error(self, quality_check):
        """Called if an exception occurs when performing the `run()` or when performing the `fix()`
        @param quality_check the involved quality check instance
        @note use `sys.exc_info()` to obtain the active exception
        """
    
    def pre_run(self, quality_check):
        """Called before running the given quality check
        @return None or one of the constants:
        - **skip_check**
          + Tells the runner not to actually run this check
        - **stop_run**
          + Tells the runner to skip this check and not try to run any other
        - **None** - has no effect
        @param quality_check the check that is about to run 
        @note default implementation has no effect
        """
        
    def post_run(self, quality_check):
        """Called after the given quality_check ran
        @return None or 
        - **stop_run**
          + Tells the runner not to run any additional checks
        @param quality_check the quality check that just ran
        @note default implementation has no effect
        """
        
    def pre_fix(self, quality_check):
        """Called before a previously failed check is to be fixed, after `pre_run()`, before `post_run()`
        @param quality_check the quality check which failed and which claims it `can_fix()` itself
        """
        
    def post_fix(self, quality_check):
        """Called after the check attempted to fix the issue
        @param quality_check that previously failed, right after the fix was applied. 
        @note the base implementation runs the check in order to bring the result up-to-date only if the check
        is still failed.
        @note is not called if the quality check threw an exception when trying to fix it. In this case, 
        `post_run(...)` will receive it accordingly"""
        
    ## -- End Interface -- @}
    
# end class IQualityCheckProvider
