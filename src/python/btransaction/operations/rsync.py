#-*-coding:utf-8-*-
"""
@package btransaction.operations.rsync
@brief An operation that uses rsync to copy or move data

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
from butility.future import str
__all__ = ['RsyncOperation']

import os
import subprocess
import time
import fcntl
import re
from select import select

from ..base import (Operation,
                    Transaction)

from butility import Path


class RsyncOperation(Operation):
    """An operation which allows to safely copy a source file or directory to a
    given destination file or directory.
    The location of the rsync-program is currently taken assumed.
    @note only works on linux (even though theoretically, rsync might exist on windows"""
    
    __slots__ = ("_source_path", 
                "_destination_path", 
                "_actual_destination_path",
                "_move_mode", 
                "_current_path",
                "_total_num_files_transferred", 
                "_num_files_transferred", 
                "_total_transferred_filesize_bytes", 
                "_transferred_filesize_bytes",
                "_current_total_transferred_filesize_bytes", 
                "_seen_progress_for_current_file",
                "_current_bandwidth", 
                "_start_time", 
                '_last_time_left_s', 
                "_process", 
                "_destination_existed",
                "_actual_destination_existed",
                "_max_bandwidth_kb"
                )

    # -------------------------
    ## @name Constants
    # @{
    
    NUM_FILES = "Number of files transferred: "
    TRANSFERRED_BYTES = "Total file size: "

    ## -- End Constants -- @}
    
    # -------------------------
    ## @name Configuration
    # @{

    name = "rsync"
    description = "Synchronize directory structures or copy files"
    
    re_is_path = re.compile(r"^/?[\w\-]+(?:/[\w\-\.]+)*$")
    re_progress = re.compile(r"(?P<bytes>\d+)\s+(?P<percent>\d+)%\s+(?P<bandwidth>\d+\.\d+\w+/\w)\s+.*")
    
    rsync_path = "/usr/bin/rsync"
    rm_path = "/bin/rm"

    ## -- End Configuration -- @}
    
    
    def __init__(self, transaction, source, destination, move=False, max_bandwidth_kb = 0):
        """initialize an rsync operation with a source and destination path.
        If move is True, the source will be deleted after a successful rsync operation.
        An operation is successful if there were no error lines in stderr of the process, and if
        If the maximum bandwidth is greater 0, the rsync operation will be using no more than the given
        bandwidth in kilobytes.
        the return code was 0."""
        super(RsyncOperation, self).__init__(transaction)

        if os.name != "posix":
            raise AssertionError("This module only works on posix systems")
        #END handle posix
        
        self._source_path = Path(source).expandvars()
        self._destination_path = self._actual_destination_path = Path(destination).expandvars()
        self._destination_existed = self._destination_path.exists()
        # rsync creates at max one parent directory if it does not exist. It will alays put 
        # directories into other directories, unless you specify a / in the end of source.
        # 
        # In case of files, it will always put them into existing directories, or rename them to the given
        # name
        if  ((self._source_path.isdir() and not self._source_path.tolinuxpath().endswith('/')) or 
            (self._source_path.isfile() and not self._destination_existed or self._destination_path.isdir())):
            self._actual_destination_path = self._destination_path / self._source_path.basename() + "/"
            # / as we have to assure it copies the contents of the directory in case of undo
        #END assure destination
        self._actual_destination_existed = self._actual_destination_path.exists()
        self._move_mode = move
        self._max_bandwidth_kb = max_bandwidth_kb
        
        self._current_path = None
        self._total_num_files_transferred = 0
        self._total_transferred_filesize_bytes = 0
        self._process = None
        self._reset_current_state()
        
    def _reset_current_state(self):
        """Reset the current values that will be counted in the following invokation"""
        self._start_time = 0
        self._num_files_transferred = 0
        self._transferred_filesize_bytes = 0
        self._current_total_transferred_filesize_bytes = 0
        self._seen_progress_for_current_file = False
        self._current_bandwidth = None
        self._last_time_left_s = None
        
    def _set_current_file(self, path):
        """set the path of the file being currently transferred, adjust state"""
        # if there is progress for the previous file, we count it
        # This will make us miss the last file, but its okay ... 
        if self._seen_progress_for_current_file:
            self._num_files_transferred += 1
            self._current_total_transferred_filesize_bytes += self._transferred_filesize_bytes
            
            self._transferred_filesize_bytes = 0
            self._seen_progress_for_current_file = False
        #END handle count
        self._current_path = path
        
    def _handle_progress_match(self, match):
        """Check the match regex and adjust our state"""
        self._current_bandwidth = match.group("bandwidth")
        self._transferred_filesize_bytes = int(match.group("bytes"))
        
    def _update_progress(self, gather_mode = False):
        """Use our state to produce a progresss
        @param gather_mode in gather mode, we will just present a count up"""
        self._abort_point()
        self._seen_progress_for_current_file = True
        prog = self._progress()
        
        if gather_mode:
            prog.set(self._num_files_transferred, message="Gathering Files ... %i" % self._num_files_transferred)
        else:
            # remaining bytes
            remaining_mbytes = (self._total_transferred_filesize_bytes - self._current_total_transferred_filesize_bytes) / 1024**2
            time_taken = max(1, time.time() - self._start_time)
            time_left_s = self._total_transferred_filesize_bytes / max(1, (self._current_total_transferred_filesize_bytes / time_taken))
            
            # remaining time
            suffix = "second"
            divisor = 1
            if time_left_s >= 60.0:
                divisor = 60
                suffix = "minute"
            #END handle suffix
            if time_left_s > 1:
                suffix += "s"
            #END handle plural
            
            if self._last_time_left_s is not None:
                time_left_s = (time_left_s + self._last_time_left_s) / 2.0      # soften jumps a bit
            #END average values
            
            msg = "Transferring %s at %s - %i files left, done in about %i %s" % (self._current_path, self._current_bandwidth, self._total_num_files_transferred - self._num_files_transferred, int(time_left_s / divisor), suffix)
            prog.set(self._num_files_transferred, message=msg)
            self._last_time_left_s = time_left_s
        #END handle gather mode
        
    def _parse_output_line(self, line):
        """Parse a single line and adjust our state accordingly
        @return 1  == file, 2  == progress, 3 == stats, False otherwise"""
        # FILENAME
        ###########
        line = line.strip() # strip trailing newline
        if self.re_is_path.match(line) is not None:
            self._set_current_file(line)
            return 1
        #END check for path
        
        # PROGRESS
        ###########
        # parse "    27131904  51%    2.44MB/s    0:00:10  "
        m = self.re_progress.match(line)
        if m:
            self._handle_progress_match(m)
            self._update_progress()
            return 2
        #END handle progress
        
        # STATS
        ###########
        if line.startswith(self.NUM_FILES):
            self._total_num_files_transferred = int(line[len(self.NUM_FILES):])
            return 3
        #END check file count
        
        if line.startswith(self.TRANSFERRED_BYTES):
            self._total_transferred_filesize_bytes = int(line[len(self.TRANSFERRED_BYTES):].split(" ")[0])
            return 3
        #END check transferred bytes
        return False
        
    def _force_removal(self, destination):
        """Forcefully delete given directory or file, linux only.
        @throws OSError"""
        self.log.info("about to remove directory at %s ... " % destination)
        rval = subprocess.call([self.rm_path, "-Rf", str(destination)])
        if rval != 0:
            raise OSError("Failed to remove file or directory that we managed to copy previously: %s" % destination)
        self.log.info("... done removing destination path")
        
    def _parse_output(self, gather_mode = False):
        """Parse the output of the rsync process and set the progress accordingly
        @param gather_mode if True, we will just hang onto the standard output, which 
            may speed up processing. This way, we only count the line actually
        @return error data, chunk-separated, lines are within the data accordingly"""
        empty_list = list()
        timeout = 0.1
        err_data = list()
        process = self._process
        
        # GATHER MODE
        ##################
        try:
            if gather_mode:
                while True:
                    line = process.stdout.readline().decode()
                    if not line:
                        return err_data
                    if self._parse_output_line(line) == 1:
                        self._update_progress(gather_mode)
                    #END update progress only if we parsed something
                #END loop forever
                return err_data
            #END handle stderr
            
            # RUN MODE
            ###########
            # Set stderr to non-blocking to allow simple reads
            fl = fcntl.fcntl(process.stderr.fileno(), fcntl.F_GETFL)
            fcntl.fcntl(process.stderr.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            while process.poll() is None:
                # stdout is in blocking mode, so we can read lines accordingly
                # try to read as many as possible
                # as long as there is someting
                while select([process.stdout.fileno()], empty_list, empty_list, timeout)[0]:
                    line = process.stdout.readline().decode()
                    if not line:
                        break
                    self._parse_output_line(line)
                #END handle standard output
            
                try:
                    # from stderr we expect not much output if at all, so poll it from time to time
                    err = process.stderr.read()
                    if err:
                        err_data.append(err)
                    #END gather errors
                except IOError:
                    # it can happen that the process goes down in the process of reading stdout
                    # Therefore we fail to read - lets just try again in this case
                    continue
                #END handle invalid reads
                
                time.sleep(timeout)
            #END while process is active
        finally:
            # if we don't close the handles, process will stay around, even if the handle gets
            # deleted. Will never get used to that, call it a bug !!! Everytime I fall for this ...
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()
        #END assure fucking pipes are closed !!!
        
        return err_data
        
    # -------------------------
    ## @name Interface Implementation
    # @{
    
    def apply(self):
        try:
            # assure that directories will have their content copied, to assure
            # the 
            source = self._source_path
            def_args = ("-a", "--append", "--progress", self._source_path, self._destination_path)
            
            def proc(args, gather_mode = False):
                self.log.info(" ".join(args))
                return subprocess.Popen(args, stdin=None, stdout=subprocess.PIPE, stderr=not gather_mode and subprocess.PIPE or None, shell=False)
            #END proc helper
            
            def handle_process(gather_mode = False):
                # PARSE OUTPUT
                ###############
                try:
                    err_chunks = self._parse_output(gather_mode)
                    if self._current_path is not None:
                        self._set_current_file(None)    # trigger the last file to be registered
                    self._process.wait()
                finally:
                    if self._process.poll() is None:
                        self._process.terminate()
                    #END assure process is terminated
                #END if process is still running here, kill it, as we are likely to be in an exceptional state (user aborted)
                
                if self._process.returncode != 0 or err_chunks:
                    raise OSError("rsync failed with error code: %i, error was \n%s" % (self._process.returncode, "".join(err_chunks))) 
                # END handle error code
                self._process = None
            #END handle process
            
            # GATHER RUN
            #############
            # Gather information about the run to determine the required needs
            args = [self.rsync_path, "--dry-run", "--stats"]
            args.extend(def_args)
            
            self._progress().setup(round_robin = True, relative=False)
            self.log.info("Calculating cost of operation ... ")
            self._process = proc(args, True)
            handle_process(gather_mode = True)
            self._reset_current_state()
            
            # VERIFY FREE SPACE IN DESTINATION
            ##################################
            # destination doesn't necessarily exist, hence we try the parent path as well
            # prefer the actual destination, in case its a dir - the parent might already be
            # on another mount
            for item in [self._destination_path, self._destination_path.dirname()]:
                if not item.exists():
                    continue
                #END handle missing items
                
                if not self._total_transferred_filesize_bytes:
                    self.log.info("Wouldn't do any work - skipping transfer operation")
                    return 
                # end abort if nothing to do
                
                fs_info = os.statvfs(item)
                free_bytes_at_destination = fs_info.f_bsize * fs_info.f_bavail
                if self._total_transferred_filesize_bytes >= free_bytes_at_destination:
                    msg = "Insufficient disk space available at %s to copy %s - require %iMB, have %iMB" % (item, self._source_path, self._total_transferred_filesize_bytes/1024**2, free_bytes_at_destination/1024**2)
                    raise OSError(msg)
                #END check free space
            #END for each item to try
            
            
            args = [self.rsync_path]
            if self._dry_run():
                args.append("--dry-run")
            #END handle dry-run
            if self._max_bandwidth_kb > 0:
                args.append("--bwlimit=%i" % self._max_bandwidth_kb)
            #END handle bandwidth limit
            args.extend(def_args)
            
            # START PROCESS
            ################
            self.log.info("Starting %s" % (" ".join(args)))
            self._progress().setup(range=(0, self._total_num_files_transferred), relative=True)
            self._start_time = time.time()
            self._process = proc(args)
            handle_process()
            
            if self._move_mode and not self._dry_run():
                self._force_removal(self._source_path)
            #END handle movemode
            
        finally:
            if self._process and self._process.poll() is not None:
                self.log.error("Terminating child forcefully")
                try:
                    self._process.kill()
                except OSError:
                    pass
                self._process = None
            #END handle process
        #END assure process is killed on error
    
    def rollback(self):
        # without destination, we couldn't fix anything anyway
        if not self._destination_path.exists():
            return
        
        # have to reproduce source from destination ?
        if not self._source_path.exists():
            if self._destination_existed:
                self.log.warn("Destination at %s existed - rollback might copy more data than expected" % self._destination_path)
            #END info
            self.log.info("Restoring source from destination ...")
            
            t = Transaction(self.log, progress = self._progress())
            type(self)(t, self._actual_destination_path + "/", self._source_path)
            
            self.log.info("rolling back rsync from %s to %s", self._actual_destination_path, self._source_path)
            if not t.apply().succeeded():
                raise IOError("Expected copy operation to succeed - rollback failed, destination data exists at %s" % self._destination_path)
            #END apply sub-transaction
        #END source doesn't exist
        
        # finally remove destination if possible
        for destination, existed in ((self._actual_destination_path, self._actual_destination_existed),
                                    (self._destination_path, self._destination_existed)):
            if existed:
                self.log.warn("Refusing deletion of destination during rollback as it existed before the rsync operation at %s" % destination)
                continue
            #END sanity check
            self._force_removal(destination)
        #END for each pair of possible paths

    ## -- End Interface Implementation -- @}
        
        
    # -------------------------
    ## @name Interface
    # @{
    
    def actual_destination(self):
        """:return: the destination that will actually receive the copy"""
        return self._actual_destination_path
        
    ## -- End Interface -- @}
