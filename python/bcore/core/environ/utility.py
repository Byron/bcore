#-*-coding:utf-8-*-
"""
@package bcore.core.environ.utility
@brief Misc utilities to help dealing with the environment

@copyright 2013 Sebastian Thiel
"""
__all__ = ['file_environment']

from contextlib import contextmanager

import bcore

@contextmanager
def file_environment(*paths, **kwargs):
    """A context manager which sets up a a context based on the given file paths. To achieve that, it will 
    alter the current global context as defined in bcore.environment to contain all environments obtained when
    creating ConfigHierarchyEnvironment instances for all the given paths.
    @return returned value is the altered bcore.environment instance, just for convenience
    @note this will temporarily change the bcore.environment, which is a rather expensive operation both in terms
    of IO and CPU
    @param paths any path that should be used to define the future context. If empty, the current 
    environment will not be altered. Each path should be a directory !
    @param kwargs valid keys are 
    + load_plugins default False, if True, plugins will be loaded for all given paths.
    @note usage: file_environment(scene, executable, cwd) as env: env.context() ..."""
    if not paths:
        yield bcore.environment
        raise StopIteration
    # end handle empty paths
    
    from .base import ConfigHierarchyEnvironment
    from bcore.processcontrol import ControlledProcessEnvironment
    
    # This is potentially dangerous, but we only assume to find the pipeline base environment which is 
    # supposed to hold the main pipeline configuration, and which must exist. We will keep this one, 
    # but recreate all others based on the input paths
    size = -1
    for index, env in enumerate(bcore.environment.stack()):
        if isinstance(env, ControlledProcessEnvironment):
            size = index + 1
            break
        # end check for special environment
    # end for each env
    assert size > -1, "Didn't find ControlledProcessEnvironment on stack"
    
    popped_environments = list()
    try:
        while len(bcore.environment) > size:
            popped_environments.append(bcore.environment.pop())
        # end pop environments
        for path in paths:
            env = bcore.environment.push(ConfigHierarchyEnvironment(path))
            if kwargs.get('load_plugins', False):
                env.load_plugins()
            # end handle plugins
        # end for each path
        yield bcore.environment
    finally:
        if len(bcore.environment) > size:
            bcore.environment.pop(until_size = size)
        # end only pop if it makes sense
        
        # put all environments back, after removing previous ones
        for env in reversed(popped_environments):
            bcore.environment.push(env)
        # end for each env

