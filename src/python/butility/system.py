#-*-coding:utf-8-*-
"""
@package butility.os
@brief utilities that deal with the operating system

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from future.builtins import str
__all__ = ['init_ipython_terminal', 'dylib_extension', 'login_name', 'uname', 'int_bits', 
           'system_user_id', 'update_env_path', 'Thread', 'ConcurrentRun', 'daemonize', 
           'TerminatableThread', 'octal']

import sys
import os
import threading
import platform
import getpass

# ==============================================================================
## @name System Related Functions
# ------------------------------------------------------------------------------
# They are platform-independent !
## @{

def init_ipython_terminal():
    """Setup ipython for use in a terminal"""
    import IPython
    if hasattr(IPython, 'Shell'):
        ips = IPython.Shell.IPShell(argv=sys.argv[:1])
        ips.mainloop()
    else:
        import IPython.frontend.terminal.interactiveshell
        IPython.frontend.terminal.interactiveshell.TerminalInteractiveShell().mainloop()
    # end handle different API versions 


def dylib_extension():
    """@return extension used for dynamically loaded libraries on the current platform
    @throws EnvironmentError if platform is unknown"""
    try:
        return {    'linux2' : "so",
                    'darwin' : "bundle",
                    'win32'   : "dll"}[sys.platform]
    except KeyError:
        raise EnvironmentError("Unknown platform: %s" % sys.platform)
    #end convert key error to environment errror


def login_name():
    """
    Cross-platform way to get the current user login

    @attention this uses an environment variable in Windows, technically allows
    users to impersonate others quite easily.
    """
    # getuser is linux only !
    # py2: str conversion required to get unicode
    if sys.platform == 'win32':
        return str(os.environ['USERNAME'])
    else:
        return str(getpass.getuser())
    #end handle platforms


def uname():
    """
    Cross-platform way to return a tuple consisting of:
    (sysname, nodename, release, version, machine), analogous to `os.uname`
    """
    try:
        pterse = platform.platform(terse=1)
    except IOError:
        # some host applications will have a directory as executable for some reason ... (katana)
        pterse = 'unknown'
    #end handle very special case
    return tuple([pterse, platform.node(),
                 platform.release(), platform.version(), platform.machine()])
    
def int_bits():
    """@return integer identifying the amount of bits used to represent an integer
    @throws EnvironmentError if the platform is neither 32 nor 64 bits
    """
    try:
        return { 9223372036854775807 : 64,
                          2147483647 : 32 }[sys.maxsize]
    except KeyError:
        raise EnvironmentError("maxint size uknown: %i" % sys.maxsize)
    #end convert keyerror to environmenterror
    
def octal(string):
    """@return the integer value represented by the given ocal value, as string.
    @param string like '0777' or '0622'
    @note useful for python 3 compatibilty with method default values"""
    res = 0
    for i, c in enumerate(reversed(string)):
        res += int(c)*(8**i)
    #end for each character
    return res
    
def system_user_id():
    """@return string identifying the currently active system user as name\@node
    @note user can be set with the 'USER' environment variable, usually set on windows"""
    ukn = 'UNKNOWN'
    username = os.environ.get('USER', os.environ.get('USERNAME', ukn))
    if username == ukn:
        username = login_name()
    # END get username from login
    return "%s@%s" % (username, platform.node())
    
def update_env_path(variable_name, path, append = False, environment = os.environ):
    """Set the given variable_name to the given path, but append or prepend the existing path
    to it using the platforms path separator.
    
    @param variable_name name of the environment variable to set
    @param path to append/prepend to the variable
    @param append if True, path will be appended to existing paths, otherwise it will be prepended
    @param environment the environment dict to adjust"""
    curval = environment.get(variable_name, None)
    # rule out empty strings
    if curval:
        if append:
            path = curval + os.pathsep + path
        else:
            path = path + os.pathsep + curval
        # END handle append
    # END handle existing path
    # environment can only contain strings - at least if used for subprocess, which must be assumed
    environment[variable_name] = str(path)

def daemonize(pid_file):
    """Daemonize ourselves to become independent of the caller
    @param pid_file path to file to prevent multiple daemons to run at once. Will always write it with our pid
    """
    
    if sys.platform.startswith("win"):
        raise OSError("Can only work on posix platforms")
    # END handle operating system
    
    try:
        # Fork a child process so the parent can exit.  This returns control to
        # the command-line or shell.    It also guarantees that the child will not
        # be a process group leader, since the child receives a new process ID
        # and inherits the parent's process group ID.  This step is required
        # to insure that the next call to os.setsid is successful.
        pid = os.fork()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if (pid != 0):
        # exit() or _exit()?
        # _exit is like exit(), but it doesn't call any functions registered
        # with atexit (and on_exit) or any registered signal handlers.   It also
        # closes any open file descriptors.  Using exit() may cause all stdio
        # streams to be flushed twice and any temporary files may be unexpectedly
        # removed.  It's therefore recommended that child branches of a fork()
        # and the parent branch(es) of a daemon use _exit().
        os._exit(0)
    # END exit 
        
    ##################
    # The first child.
    ##################
    # To become the session leader of this new session and the process group
    # leader of the new process group, we call os.setsid(). The process is
    # also guaranteed not to have a controlling terminal.
    os.setsid()

    # Is ignoring SIGHUP necessary?
    #
    # It's often suggested that the SIGHUP signal should be ignored before
    # the second fork to avoid premature termination of the process.    The
    # reason is that when the first child terminates, all processes, e.g.
    # the second child, in the orphaned group will be sent a SIGHUP.
    #
    # "However, as part of the session management system, there are exactly
    # two cases where SIGHUP is sent on the death of a process:
    #
    #    1) When the process that dies is the session leader of a session that
    #        is attached to a terminal device, SIGHUP is sent to all processes
    #        in the foreground process group of that terminal device.
    #    2) When the death of a process causes a process group to become
    #        orphaned, and one or more processes in the orphaned group are
    #        stopped, then SIGHUP and SIGCONT are sent to all members of the
    #        orphaned group." [2]
    #
    # The first case can be ignored since the child is guaranteed not to have
    # a controlling terminal.   The second case isn't so easy to dismiss.
    # The process group is orphaned when the first child terminates and
    # POSIX.1 requires that every STOPPED process in an orphaned process
    # group be sent a SIGHUP signal followed by a SIGCONT signal.   Since the
    # second child is not STOPPED though, we can safely forego ignoring the
    # SIGHUP signal.    In any case, there are no ill-effects if it is ignored.
    #
    # import signal           # Set handlers for asynchronous events.
    # signal.signal(signal.SIGHUP, signal.SIG_IGN)

    try:
        # Fork a second child and exit immediately to prevent zombies.   This
        # causes the second child process to be orphaned, making the init
        # process responsible for its cleanup.   And, since the first child is
        # a session leader without a controlling terminal, it's possible for
        # it to acquire one by opening a terminal in the future (System V-
        # based systems).    This second fork guarantees that the child is no
        # longer a session leader, preventing the daemon from ever acquiring
        # a controlling terminal.
        pid = os.fork() # Fork a second child.
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if (pid != 0):
        # exit() or _exit()?     See below.
        os._exit(0) # Exit parent (the first child) of the second child.
    # END exit second child

    # Decouple stdin, stdout, stderr
    fd = os.open(os.devnull, os.O_RDWR) # standard input (0)
    
    # Finally, write our PID file
    open(pid_file, 'wb').write(str(os.getpid()))

    # Duplicate standard input to standard output and standard error.
    os.dup2(fd, 1)           # standard output (1)
    os.dup2(fd, 2)           # standard error (2)

# -- End System Related Functions -- @}


# ==============================================================================
## @name Types
# ------------------------------------------------------------------------------
## @{

class Thread(threading.Thread):
    """Applies a few convenience fixes"""
    __slots__ = ()

    def start(self):
        """Start the thread
        @return self"""
        super(Thread, self).start()
        return self
        
# end class Thread


class ConcurrentRun(Thread):
    """Execute a function in its own thread and provide the result.
    Note: Currently this is implemented such that each run starts its own thread, 
    which is expensive. For many concurrent operations, a thread pool should be used
    
    Usage: ConcurrentRun(my_method).start().result() or
    ConcurrentRun(my_method).start() # and forget about it

    @note python will terminate even though a concurrent 
    """
    
    __slots__ = (
                '_result',  # result of our operation
                '_exc',     # the exception thrown
                '_fun',     # method to run
                '_log',     # optional logger instance
                )
    
    def __init__(self, fun, logger = None, daemon=False):
        """Initialize this instance with the function to execute
        @param fun callable to execute
        @param logger a logger instance
        @param daemon if True, a running Thread will prevent python to exit"""
        super(ConcurrentRun, self).__init__()
        self.daemon = daemon
        self._result = None
        self._exc = None
        self._fun = fun
        self._log = logger
        
    def _assure_joined(self):
        try:
            self.join()
        except RuntimeError: # on joining before started
            pass
        #END handle exception
        
    def run(self):
        try:
            self._result = self._fun()
        except Exception as exc:
            self._exc = exc
            if self._log is not None:
                self._log.critical("%s failed" % str(self._fun), exc_info=1)
            #END log errors
        #END handle exception
        
    #{ Interface
    
    def result(self):
        """@return the result of the function we ran. Will block until we are done
        with our computation"""
        self._assure_joined()
        return self._result
    
    def error(self):
        """@return exception thrown or None if there was no error"""
        self._assure_joined()
        return self._exc
    
    #} END interface


class TerminatableThread(Thread):
    """A thread able to terminate itself on behalf of the user.
    
    Terminate a thread as follows:
    
    t.stop_and_join()
    
    Derived classes call _should_terminate() to determine whether they should 
    abort gracefully
    """
    __slots__ = '_terminate'
    
    def __init__(self, *args, **kwargs):
        super(TerminatableThread, self).__init__(*args, **kwargs)
        self._terminate = False
        

    # -------------------------
    ## @name Subclass Interface
    # @{
    
    def _should_terminate(self):
        """@return True if this thread should terminate its operation immediately"""
        return self._terminate
        
    ## -- End Subclass Interface -- @}
        
    # -------------------------
    ## @name Interface
    # @{
    
    def cancel(self):
        """Schedule this thread to be terminated as soon as possible.
        @note this method does not block."""
        self._terminate = True
    
    def stop_and_join(self):
        """Ask the thread to stop its operation and wait for it to terminate
        :note: Depending on the implenetation, this might block a moment"""
        self.cancel()
        self.join()

    ## -- End Interface -- @}

# end class TerminatableThread

## -- End Types -- @}
