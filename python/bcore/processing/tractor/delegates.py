#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.delegates
@brief Contains delegates suitable for use with tractor and particular applications

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorDelegateMixin', 'NukeTractorDelegate', 'MayaBatchDelegate', 'KatanaTractorDelegate']

import re
import os
import sys
import subprocess
import json
import urllib2
import logging
import select

import bcore
from bcore.utility import DictObject


from bcore.processcontrol import (
                                    ProcessControllerDelegate,
                                    MayaProcessControllerDelegate,
                                    KatanaControllerDelegate
                                )

from .alf.generators import TractorCmdGeneratorBase


log = new_service(bcore.ILog).new('bcore.processing.tractor.delegates')


class TractorDelegateMixin(object):
    """A delegate of the ProcessControl framework which specifically deals with the needs of the farm
    
    # Features
    
    - Provide suitable limits for memory and amount of threads
    - Allow to inject progress for tractor by parsing process output
    
    This implementation is meant for subclasses which can specialize particular aspects of this implementaiton.
    Those subclasses must also inherit from their original wrapper implementation to assure all other aspects
    are also handled correctly. 
    
    @note If in doubt, inherit from this Mixin type first, be sure to inherit from ProcessControllerDelegate
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Classifications that can be parsed by subclasses
    ## Indicates the line is progress
    LINE_PROGRESS = 'progress'
    
    ## Indicates the line contained an error code
    LINE_FATAL = 'fatal'
    
    ## Indicates nothing interesting was parsed
    LINE_NOOP = 'noop'
    
    ## -- End Configuration -- @}
    
    
    ## Class-level variable to keep information about whether we should get input from stdin
    ## Should be instance level, but we are created multiple times and can't really keep state unless
    ## its 'global'. As we are a singleton per defintiion, this is okay though
    _read_stdin = False
    
    
    ## Tractor delegates will always have to restore their context from the input paths
    ## Subclasses can of course decide differently and be more specific, if needed
    context_from_path_arguments = True
    
    # -------------------------
    ## @name Utilities
    # @{
    
    @classmethod
    def _blade_url(cls):
        """@return url under which blade status can be received"""
        return 'http://localhost:9005/blade/status'
    
    def _query_blade_information(self):
        """@return a dict object with all blade information, as obtained using the tractor rest API, or None
        if a blade connection could not be established"""
        url = self._blade_url()
        log.debug("About to query blade status information from '%s' - could block if something is wrong with proxy", url)
        
        # Make sure we access localhost without proxy, no matter what the configuration says
        urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler({})))
        
        try:
            return DictObject(json.load(urllib2.urlopen(url)))
        except Exception, err:
            log.error("Failed to query blade", exc_info=True)
            return None
        # end handle error
        
    ## -- End Utilities -- @}
    
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    def _insert_limits(self, max_mem_gb, max_cores, args, env, blade_data):
        """Called to manipulate the about-to-be-started process no use more than max_mem memory and max_cores
        cores.
        @param max_mem_gb float of precomputed maximum amount of memory to use in gigabytes
        @param max_cores precomputed maximium amount of cores to use
        @param args a list of arguments given to the application. Adjust it as required to setup the 
        constraints
        @param env the environment dictionary to be given to the process. Adjust it as required to 
        setup the constraints
        @param blade_data a DictObject with the json return value obtained from the blade status 
        @note subclasses may ignore this call (or not implement it) if limits are not easily set. In this 
        case the default implementation will attempt to set limits using the operating system"""
        
        
    def _classifiy_line(self, line):
        """Called for each line of output of our child process for the subclass to analyse.
        @param line a line (with newline at the end) which is to be checked for interesting information.
        The line is NOT stripped.
        @return  (LINE_*, value), a tuple of LINE_CONSTANT and value 
        
        - LINE_PROGRESS, progress indicates progress was found, progress is a value from 0 to 100
        - LINE_FATAL, returncode a warning or error which should cause the process return code to be altered
        to the given one
        - LINE_NOOP, None, indicates the line didn't trigger anything"""
        return self.LINE_NOOP, None
        
    ## -- End Subclass Interface -- @}
    
    
    # -------------------------
    ## @name Interface Implementation
    # @{
    
    def should_spawn_process(self):
        """@return always true as we wish to parse process output"""
        return True
        
    def process_filedescriptors(self):
        """For now we are only interested in stdout"""
        return (None, subprocess.PIPE, subprocess.PIPE)
        
    def communicate(self, process):
        """communicate with process and read everything from its stdout.
        Call our subclass's functions classify it and insert the appropriate line into our own output stream.
        By default, we will just copy the line from the process's stdout into our own one"""
        assert process.stdout is not None, 'should have a file descriptor as stdout'
        
        output = sys.stdout.write
        noop, progress, fatal = self.LINE_NOOP, self.LINE_PROGRESS, self.LINE_FATAL
        progress_format = "TR_PROGRESS %03i%%%s"
        output(progress_format % (0, os.linesep))
        
        def handle_line(line):
            """Handler for a line of output"""
            try:
                cmd, value = self._classifiy_line(line)
            except Exception:
                sys.stderr.write("WRAPPER: Failed to parse line: %s" % line) 
                cmd, value = self.LINE_NOOP, None
            # end handle exception
            
            if cmd == progress:
                output(progress_format % (value, os.linesep))
            elif cmd == fatal:
                output('TR_EXIT_STATUS %03i%s' % (value, os.linesep))
            else:
                assert cmd == noop, "Line command %s is unknown" % cmd
            # end handle classification
            
            # copy line to output
            output(line)
        # end handler
                  
        if hasattr(select, 'poll'):
            fdmap = { process.stdout.fileno() : process.stdout,
                      process.stderr.fileno() : process.stderr }
            
            poll = select.poll()
            READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
            CLOSED = select.POLLHUP | select.POLLERR
            
            poll.register(process.stdout, READ_ONLY)
            poll.register(process.stderr, READ_ONLY)
            
            closed_streams = set()
            while True:
                # no timeout
                poll_result = poll.poll()
                for fd, result in poll_result:
                    if result & CLOSED:
                        closed_streams.add(fd)
                    else:
                        # there is something to read - this blocks, but its okay
                        handle_line(fdmap[fd].readline())
                    # end handle closed stream
                # end for each poll-result tuple
                
                if len(closed_streams) == len(fdmap):
                    break
                # end its all done
            # end endless loop
        else:
            # On windows, this doesn't work and we only read from stdout. On linux, we read from whichever
            # channel there is 
            for line in process.stdout:
                handle_line(line)
            # end for each line
        # end initialiez poll
        
        return super(TractorDelegateMixin, self).communicate(process)
        
    def handle_argument(self, arg, kvstore):
        """Parses own arguments"""
        if arg == TractorCmdGeneratorBase.read_from_stdin_argument:
            type(self)._read_stdin = True
        else:
            return super(TractorDelegateMixin, self).handle_argument(arg, kvstore)
        # end handle argument

    def pre_start(self, executable, env, args, cwd):
        """Qeries the blade to figure out the amout of resource we can use at max.
        @todo use our own API to query blade information"""
        # handle stdin and set the respective environment variables
        # NOTE: have to read BEFORE we query the blade. Otherwise the blade will still send us 
        # data from stdin (optional), and block until someone read it. In that time, it will not process
        # any other queries, and we block as well. Deadlock ... .
        if self._read_stdin:
            log.debug("Reading data from stdin to provide it to upcoming process")
            env[TractorCmdGeneratorBase.data_storage_env_var] = sys.stdin.read()
        #end handle stdin
        
        data = self._query_blade_information()
        if data:
            mem_gb_max = data.memFree / float(data.slotsMax)
            cores_max = int(data.cpuCount / float(data.slotsMax))
            
            log.log(logging.TRACE, 'Slots = %s', data.slotsMax)
            log.log(logging.TRACE, 'mem_gb_max = %s = %s / data.slotsMax', mem_gb_max, data.memFree)
            log.log(logging.TRACE, 'cores_max = %s = %s / data.slotsMax', cores_max, data.cpuCount)
            
            self._insert_limits(mem_gb_max, cores_max, args, env, data)
        else:
            log.warning("Limits are not set as we couldn't communicate to the blade via URL '%s'", self._blade_url())
        # end handle data available
        return super(TractorDelegateMixin, self).pre_start(executable, env, args, cwd)
        
    ## -- End Interface Implementation -- @}
        
# end class TractorDelegateMixin


class NukeTractorDelegate(TractorDelegateMixin, ProcessControllerDelegate):
    """A delegate specialized on dealing with the nuke process on the farm"""
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    read_error = "Read error: No such file or directory"
    
    ## Exit code to be injected in case a file could not be read
    read_error_return_code = 22
    re_parse_frame = re.compile(r"^Frame \d+ \((\d+) of (\d+)\)$")
    
    ## -- End Configuration -- @}

    # -------------------------
    ## @name Subclass Implementation
    # @{
    
    def _classifiy_line(self, line):
        """Parse progress"""
        match = self.re_parse_frame.match(line)
        if match:
            first, last = int(match.group(1)), int(match.group(2))
            return self.LINE_PROGRESS, (first / float(last)) * 100
        elif self.read_error in line:
            return self.LINE_FATAL, self.read_error_return_code
        # end handle match
        return super(NukeTractorDelegate, self)._classifiy_line(line)
        
    def _insert_limits(self, max_mem_gb, max_cores, args, env, blade_data):
        """Add limits for memory and threads"""
        args[:0] = ['-m', str(max_cores),
                    '-c', '%ik' % (max_mem_gb * 1024**2)]
        
    ## -- End Subclass Implementation -- @}
    
# end class NukeTractorDelegate


class MayaBatchDelegate(TractorDelegateMixin, MayaProcessControllerDelegate):
    """A delegate able to execute any code in maya by examining it coming in from stdin"""
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{
    
    ## Should match python errors, logging errors and mel errors
    ## Do not abort on Error: ... for now we usually get those
    re_parse_error = re.compile(r"ERROR |(Exception):")
    
    ## The exit code to be injected in case there was an exceptionn in the script
    error_return_code = 234
    
    ## -- End Configuration -- @}
    
    def _classifiy_line(self, line):
        """Parse errors"""
        match = self.re_parse_error.search(line)
        if match:
            return self.LINE_FATAL, self.error_return_code
        # end handle match
        return super(MayaBatchDelegate, self)._classifiy_line(line)

# end class MayaBatchDelegate


class MayaRenderDelegate(TractorDelegateMixin, MayaProcessControllerDelegate):
    """A delegate to parse progress from maya renderings"""
    __slots__ = ()
    
    re_match_percent = re.compile('(\d+\.\d)%')
    
    def _classifiy_line(self, line):
        """Parse progress"""
        match = self.re_match_percent.search(line)
        if match:
            # now it would be great to know start-end. We could actually parse it using argparse for instance
            # but ... another time
            # TODO: improve this implementation - we could get actual percentage in fine granularity !
            
            # This will match % as provided by MR.
            # For now there is not sw handling
            return self.LINE_PROGRESS, int(float(match.group(1)))
        # end handle match
        return super(MayaRenderDelegate, self)._classifiy_line(line)
    
    def _insert_limits(self, max_mem_gb, max_cores, args, env, blade_data):
        """Setup limits for the maya render commands. No matter which renderer is used, we will just set up 
        all the limits we know about"""
        max_mem_MB = int(max_mem_gb * 1024)
        args[0:0] = [
            '-mr:memory', str(max_mem_MB),
            '-mr:renderThreads', str(max_cores),
            '-sw:mm', str(min(max_mem_MB, 2048)),   # yes, there is a limit of the attribute, incredible
            # The idea would be to sooner than later just use our own batch scripts for rendering, dealing
            # with settings and assets properly right away.
            #'-sw:n', str(max_cores)                 # even though this is given with -r sw -help, it doesnt work
            
            # Additionally, make sure we are verbose enough to get progress information
            '-mr:verbose', str(5),
        ]
        

# end class MayaRenderDelegate


class KatanaTractorDelegate(TractorDelegateMixin, KatanaControllerDelegate):
    """A delegate to setup katana limits when it is farmed."""
    __slots__ = ()
    
    ## Maximum amount of memory to reserve for OS operations
    reserved_system_memory_gb = 2.0
    
    def _insert_limits(self, max_mem_gb, max_cores, args, env, blade_data):
        """Setup prman limits using environment variables"""
        # We have a total of 2GB for the system to split up on all slots
        total_mem_relative = (blade_data.memFree - self.reserved_system_memory_gb) / blade_data.memFree
        max_mem_relative = total_mem_relative / blade_data.slotsMax
        env['RMAN_CPU_COUNT'] = str(max_cores)
        env['RMAN_MEM_LIMIT'] = str(max_mem_relative)
        
        log.log(logging.TRACE, 'rman_mem_limit = %s = %s / data.slotsMax', max_mem_relative, total_mem_relative)


# end class KatanaTractorDelegate
