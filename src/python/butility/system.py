#-*-coding:utf-8-*-
"""
@package butility.os
@brief utilities that deal with the operating system

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['init_ipython_terminal', 'dylib_extension', 'login_name', 'uname', 'int_bits', 
           'system_user_id', 'update_env_path', 'Thread', 'ConcurrentRun']

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
    if sys.platform == 'win32':
        return os.environ['USERNAME']
    else:
        return getpass.getuser()
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
                          2147483647 : 32 }[sys.maxint]
    except KeyError:
        raise EnvironmentError("maxint size uknown: %i" % sys.maxint)
    #end convert keyerror to environmenterror
    
    
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
        except Exception, exc:
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

## -- End Types -- @}
