#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.base
@brief A module with base implelementations and general utilities

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorSubmitter', 'TractorJobID']

import sys
import os
import re
import subprocess


from ..alf import (
                    AlfSerializer,
                  )

from ..schema import tractor_schema
from bcore.core.component import EnvironmentStackContextClient
from bcore.utility import (
                            LazyMixin,
                            login_name
                       )
from cStringIO import StringIO

from bcore.path import Path

class TractorJobID(int):
    """A class encapsulating a JobID as used by tractor
    @note type serves as standin just in case we want to provide a more elaborate notion to allow 
    querying the job state later (like a 'future' in threaded frameworks, which represents work to be ready
    after a certain time)"""
    __slots__ = ()
    
    ## An invalid JobID, useful for error codes
    invalid = -1

# end class JobID


class TractorSubmitter(EnvironmentStackContextClient, LazyMixin):
    """A simple utility which submits JobTrees to tractor
    
    @note We will read our configuration from the kvstore, but never write it
    @note for now there is no generalized interface"""
    __slots__ = (
                    '_priority_map'  ## mapping between priorities and integer values
                )
    
    _schema = tractor_schema
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Priority constants, which are mapped to actual priority values
    PRIORITY_LOW = 'low'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    
    ## A map for priorities, will soon be dynamic using the kvstore
    priorities = [PRIORITY_HIGH, PRIORITY_NORMAL, PRIORITY_LOW]
    
    ## The ID referring to the tracor spooler
    spooler_id = 'tractor-spool'
    
    # parses OK job script accepted, jid: 1307140009
    re_job_id = re.compile('\d{10}')
    ## -- End Configuration -- @}


    def _set_cache_(self, name):
        if name == '_priority_map':
            self._priority_map = self.context_value().submission.priority
        else:
            super(TractorSubmitter, self)._set_cache_(name)
        #end handle name
    
    # -------------------------
    ## @name Interface
    # @{
    
    def submit(self, job, priority=PRIORITY_NORMAL, paused=False, resolve_references=True):
        """Submit the given job alf operator to tractor
        @param job Alf Operator of type Job, or a string or Path instance pointing to the .alf file to submit
        @param priority one of the priority constants
        @param paused if True, the task will be paused when it arrives on the queue
        @param resolve_references if True, and if the input is a Job instance, the AlfSerializer will 
        resolve string references to their actual instances. This may raise if references are invalid.
        You should keep this check unless you are absolutely sure that you have set it up correctly.
        @return instance of typoe TractorJobID
        @throw ValueError if the submission failed"""
        
        # Serialize the job into a temporary file and submit it
        jobstring = job
        if not isinstance(job, basestring):
            sio = StringIO()
            AlfSerializer().init(sio.write).serialize(job, resolve_references=resolve_references)
            jobstring = sio.getvalue()
        # end assure file is closed in time (and flushed)
        
        priority_value = self.priority_value(priority)
        if paused:
            # offset priority to allow priority of 0
            priority_value = -priority_value - 1
        # end handle paused
        
        raise NotImplementedError("Re-implement tractor RPC or call the tractor spooler to make submission work")
        # engine = EngineTractorConnection()
        # res = engine.spool_job(jobstring_or_path = jobstring, priority = priority_value, job_owner = login_name(),
        #                         cwd = os.getcwd())
        
        if not hasattr(res, 'jid') or not res.jid:
            raise ValueError(res.msg)
        # end handle message
        
        return TractorJobID(res.jid)
        
        
    def priority_value(self, priority):
        """@return value corresponding to the given priority constant"""
        assert priority in self.priorities, 'invalid priority: %s' % priority
        assert priority in self._priority_map, 'priority not found in mapping - data inconsisent ?'
        return self._priority_map[priority]
    ## -- End Interface -- @}
        

# end class TractorSubmitter
