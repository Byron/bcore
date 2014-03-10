#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.generators.maya
@brief Submission of maya scenes for rendering or for performing batch operations

@note This module needs to be usable anywhere, and may not rely on being run from the nuke host application
@copyright 2013 Sebastian Thiel
"""
__all__ = ['MayaBatchTaskGenerator', 'MayaRenderTaskGenerator']

from bcore.core.kvstore import KeyValueStoreSchema

from .cmdbase import TractorCmdGeneratorBase
from .types import (
                    JobGenerator,
                    FrameSequenceGenerator
                  )
from .. import (
                    Task,
                    Cmd,
                    Tags,
                  )
import copy
from bcore.path import Path


class MayaTaskBase(TractorCmdGeneratorBase):
    """Provides general implementations and commmon variables"""
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## If true, _is_valid_context will only return True if we have a job file set
    needs_job_file = True
    
    ## -- End Configuration -- @}
    
    variable_field_schema = TractorCmdGeneratorBase._merge_schemas((JobGenerator.variable_field_schema,
                                                                   FrameSequenceGenerator.variable_field_schema))
    
    
    def _is_valid_context(self, context):
        """@return True if we are to handle a maya file"""
        data = self._context_value(context)
        
        if not data.job.file:
            return not self.needs_job_file
        # end allow no file set
        
        return data.job.file.ext() in ('.ma', '.mb')
    
    
    # -------------------------
    ## @name Utilities
    # @{
    
    def _find_project_directory(self, directory):
        """Starting at the given directory, try to find a workspace.mel moving upwards in the folder hierarchy
        @return directory containing workspace.mel file, or None if none was found"""
        while directory.dirname() != directory:
            path = directory / 'workspace.mel'
            if path.isfile():
                return directory
            directory = directory.dirname()
        # end while traversing upwards
        return None
        
    def _project_args(self, filepath):
        """@return a list of arguments to set the project as automatically determined for the given filepath, 
        or an empty list if none was found"""
        project_directory = self._find_project_directory(filepath.dirname())
        if project_directory is not None:
            return ['-proj', project_directory]
        return list()
        
    ## -- End Utilities -- @}

# end class MayaTaskMixin


class MayaBatchTaskGenerator(MayaTaskBase):
    """Setup a task which starts maya batch and optionally openes a file beforehand.
    
    We support chunking on demand, and will load a maya file if it is set.
    
    Custom maya batch commands are encouraged to derive from this one and merge their own variable_field_schema
    to add their own custom attributes. Those will be picked up and written into the input stream for your
    custom command to digest.
    
    The workspace will be automatically set, if possible.
    
    Custom types must override _default_context() and put the command they want to execute in python
    """
    __slots__ = ()
    
    
    # -------------------------
    ## @name Configuration
    # @{
    
    cmd_id = 'tractor-maya-batch'
    
    needs_job_file = False
    
    static_field_schema = KeyValueStoreSchema('maya', dict(cmd = dict(
                                                                            python = str()        # the python command to evaluate
                                                                        )
                                                                )
                                                            )
    ## -- End Configuration -- @}
    
    def _tree_iterator(self, context):
        data = self._context_value(context)
        
        assert data.maya.cmd.python, "require python command to be set, do this in _default_context() of your subclass"
        
        # Hand all context data over to command
        cmd = copy.deepcopy(self._cached_wrapped_command(data.job.file, context.data()))
        
        args = [
            '-batch',
            '-script', Path(__file__).dirname().abspath() / 'maya-entrypoint.mel'
        ]
        
        # Workspace
        ###########
        if data.job.file:
            args += self._project_args(data.job.file)
        # end handle file
        
        if data.job.file:
            args.extend(['-file', data.job.file])
        # end handle file
        
        cmd.args += args
        yield Task(title='maya batch', cmds = cmd)

# end class MayaBatchTaskGenerator


class MayaRenderTaskGenerator(MayaTaskBase):
    """Setup a task which allows to perform a rendering with maya
    
    For now we only support rendering with the settings supplied in the file, and we need a file to work.
    Chunks are optional, but are highly recommended.
    
    The workspace will be automatically set
    
    @note for now there is no support for custom callbacks, using similar means as MayaBatchTaskGenerator for 
    instance, as we don't know how it will be with the asset management system yet.
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    cmd_id = 'tractor-maya-render'
    
    
    static_field_schema = KeyValueStoreSchema('maya',       { 'render' : {
                                                                'image_output_directory' : Path() # directory into which images are put
                                                                }
                                                            })
    
    ## -- End Configuration -- @}
    
    def _tree_iterator(self, context):
        data = self._context_value(context) # dynamic
        assert data.job.file, 'require a job file to be set for rendering'
        
        # note: limits are set by the delegate
        cmd = copy.deepcopy(self._cached_wrapped_command(data.job.file))
        
        args = list()
        
        # CHUNKING
        ###########
        if context.has_value('frame.chunk'):
            args += [
                '-s', data.frame.chunk.first,
                '-e', data.frame.chunk.last,
                '-b', data.frame.chunk.step
            ]
        # end use chunk only if it is there
        
        # Workspace
        ###########
        args += self._project_args(data.job.file)
        
        # Output
        ########
        if data.maya.render.image_output_directory:
            args += ['-rd', data.maya.render.image_output_directory]
        # end handle image output
        
        args += [
            '-verb',            # verbosely show mel commands executed to render
            '-r', 'file',       # use renderer setup in the file
            
            # last comes the file to render
            data.job.file
        ]
        
        cmd.args += args
        
        # If we have chunks 
        yield Task(title='maya render (file)', cmds = cmd)

# end class MayaRenderTaskGenerator

