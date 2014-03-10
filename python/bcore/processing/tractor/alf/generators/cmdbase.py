#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.generators.cmdbase
@brief A modul for holding the tractor generator handling command execution based on processcontrol

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorCmdGeneratorBase']

import pickle
import binascii


import bcore
from bcore.core.component import EnvironmentStackContextClient
from bcore.core.kvstore import (
                                KeyValueStoreSchema,
                                AnyKey,
                            )
from bcore.core.environ import file_environment
from .base import NodeGeneratorBase
from ..   import (
                    Cmd,
                    RemoteCmd,
                    Tags
                  )
from bcore.processcontrol import (
                                    PackageDataIteratorMixin,
                                    package_schema,
                                    ProcessControllerDelegate
                               )

log = new_service(bcore.ILog).new('bcore.processing.tractor.submission.base')


class TractorCmdGeneratorBase(NodeGeneratorBase, EnvironmentStackContextClient, PackageDataIteratorMixin):
    """A utility to help creating Cmd operators which are using process control to run an executable on the farm.
    
    We also support querying all used packages in the process to associate tags with them.
    This allows for automated license tracking in the very foundation of the system. It also means 
    we have to make licensed software available only in the files that actually need them."""
    __slots__ = (
                    '_cmd_template'  # A cached command instance obtained after _wrapped_command()
                )
    
    # -------------------------
    ## @name Constants
    # @{
    
    ## A marker to indicate the delegate has to read from stdin
    read_from_stdin_argument = 'read-from-stdin'
    
    ## The environment variable which will keep the serialized data for later consumption in-process
    data_storage_env_var = 'BCORE_TRACTOR_CUSTOM_DATA'
    
    ## -- End Constants -- @}
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Context schema we use to know which package uses which id
    _schema = PackageDataIteratorMixin.new_controller_schema({
                                                            'requires' : package_schema['requires'],
                                                            'tractor': {
                                                                  # A list of tags to assign to the package when
                                                                  # involved in a tractor command
                                                                  'tags': Tags,
                                                                  # A list of services that should automatically be added
                                                                  # Those must match with whatever is configured in tractor
                                                                  # This could also be a show, for instance
                                                                  'service' : Tags
                                                              },
                                                            })
    
    ## The name of the executable to execute. It must be defined in the ProcessController 
    ## framework's configuration
    ## @note must be set by subclass
    cmd_id = None
    
    ## -- End Configuration -- @}
    
    
    # -------------------------
    ## @name Utilities
    # @{
    
    @classmethod
    def serialize_data(cls, data):
        """Serialize the given data dictionary into a repreentation that can be deserialized using
        deserialize_data()
        @param cls
        @param data a dictionary of data that is to be serialized
        @return a hexadecimal string
        @note it would be nicer for debugging if this was human-readable. Could be achieved by proper escaping,
        or by using a spool file that people can look at and change"""
        return binascii.b2a_hex(pickle.dumps(data))
        
    @classmethod
    def deserialize_data(cls, string):
        """@return dict object deserialized from string
        @param cls
        @param string a string created from serialize_data"""
        return pickle.loads(binascii.a2b_hex(string))
    
    ## -- End Utilities -- @}
    
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    @classmethod
    def _cmd_type(cls):
        """@return the type of command to use.
        @note defaults to RemoteCmd"""
        return RemoteCmd
        
    def _cached_wrapped_command(self, path, data_for_stdin = None):
        """Similar to _wrapped_command(), but will return a cached instance, instead of creating a new one
        @warning The value is cached in the _cmd_template attribute.
        Delete it if the context matters and changed, or use _wrapped_command() instead"""
        if hasattr(self, '_cmd_template'):
            return self._cmd_template
        # end handle cache
        self._cmd_template = self._wrapped_command(path, data_for_stdin)
        return self._cmd_template
        
    def _tags_and_services_from_packages(self, package_name):
        """@return a list of tags and list of service expressions to use to mark the package as well as all 
        its requirements. List can contain duplicates, but those will be deduplicated upon assignment
        @param package_name name of the root package
        @note will use the current environments context for the mapping"""
        tags = list()
        services = list()
        for pdata, pname in self._iter_package_data(self.context_value(), package_name):
            tags.extend(pdata.tractor.tags)
            services.extend(pdata.tractor.service)
        # end for each package item
        return tags, services
        
    def _wrapped_command(self, path, data_for_stdin = None):
        """@return a new Cmd instance whose executable is set to the one of our cmd id. Its tags will include
        all tags that where mapped to the packages currently in use. Additionally the service expression will be filled
        with a comma-separated list of all service keys accumulated from all packages the path requires
        @param path to the file that you would want to execute using a command with your cmd_id. The context
        at the file's location will be used accordingly.
        If the path is None or not set, a default version of the wrapper will be used as retrieved from 
        repository/bin/...
        @param data_for_stdin if not None, it is expected to be any pickle-able structure that should be fed
        to the command using stdin. Note that this requires a suitable delegate to handle the stdin accordingly,
        the default TractorCompatible delegate will do that out of the box.
        @warning this method is very slow, see _cached_wrapped_command()"""
        assert self.cmd_id, "cmd_id must be set in subclass"
        
        paths = []
        if path:
            paths.append(path)
        # end use path
        
        # Make sure we use the enviroment at path (if available) to find the executable
        # The location of the executable is not part of the equation yet
        with file_environment(*paths):
            # We assume services ordered from most specialised to most general, which is exactly what we want
            # here
            executable = None
            bases = list()
            for svc in services(bcore.IDirectoryService):
                try:
                    base = svc.path(bcore.IProjectService.PATH_EXECUTABLES)
                    bases.append(base)
                    executable = base / self.cmd_id
                except ValueError:
                    continue
                # ignore id not understood
                if executable.exists():
                    break
                # end handle executable
                log.debug("dropped executable '%s' as it wasn't accessible", executable) 
                executable = None
            # end for each service
            
            assert executable is not None, "Couldn't find executable path for command with id '%s', searched %s" % (self.cmd_id, ','.join(bases))
            
            # At least for the executable, create a new environment in case we didn't set it previously
            if not paths:
                paths.append(executable.dirname())
            else:
                # Otherwise we have an environment set already, and will just do nothing next time.
                # We assume the executable to do not much of a difference
                paths = list()
            # end handle paths
            
            with file_environment(*paths):
                # assure we initialize this controller with a base path our own executable, using the cmd id of our subclass
                # to define the actual executable that we can then query
                # ---trace to assure we see what's actually executed
                cmd = self._cmd_type()(executable, '%s%s' % (ProcessControllerDelegate._wrapper_arg_prefix,
                                                             ProcessControllerDelegate._wrapper_logging_levels[0]))
                if data_for_stdin:
                    cmd.args.append('%s%s' % (ProcessControllerDelegate._wrapper_arg_prefix, 
                                              self.read_from_stdin_argument))
                # end mark that the delegate has to read from stdin
                
                tags, svcs = self._tags_and_services_from_packages(self.cmd_id) 
                cmd.tags = tags
                cmd.service = ','.join(svcs)
                if data_for_stdin is not None:
                    cmd.msg = self.serialize_data(data_for_stdin)
                # end 
                return cmd
            # end within (possibly) executable environment
        # end within a path environment
    
    ## -- End Subclass Interface -- @}

# end class TractorCmdOperator


