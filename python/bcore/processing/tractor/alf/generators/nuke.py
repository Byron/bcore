#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.generators.nuke
@brief Submission of nuke scripts

@note This module needs to be usable anywhere, and may not rely on being run from the nuke host application
@copyright 2013 Sebastian Thiel
"""
__all__ = ['NukeRenderTaskGenerator']


from .cmdbase import TractorCmdGeneratorBase
from ...delegates import NukeTractorDelegate
from .types import (
                        FrameSequenceGenerator,
                        JobGenerator,
                   )
from .. import (
                    Task,
                    Cmd,
                  )
import copy

class NukeRenderTaskGenerator(TractorCmdGeneratorBase):
    """A task to perform nuke rendering using process control.
    
    We take care of building a commandline suitable for rendering a nuke scene in a certain frame range
    """
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{
    
    ## Name of the program we use for rendering. Must be configured in process controller package database.
    cmd_id = 'tractor-nuke'
    
    ## limit tag (for licensing). Must match with limits.config in tractor
    limit_nuke_render = 'nuke_render'
    limit_nuke_interactive = 'nuke_interactive'
    
    ## We support frame ranges and a single nuke file
    variable_field_schema = TractorCmdGeneratorBase._merge_schemas((JobGenerator.variable_field_schema,
                                                                   FrameSequenceGenerator.variable_field_schema))
    
    ## -- End Configuration -- @}
    
    def _is_valid_context(self, context):
        """@return True if we are to handle a nuke file"""
        return self._context_value(context).job.file.ext() == '.nk'
    
    def _tree_iterator(self, context):
        """@return a python iterator which yields one nuke task with the respective command
        @note we don't set constraints, this is happening when rendering on the farm"""
        data = self._context_value(context)
        cmd = copy.deepcopy(self._cached_wrapped_command(data.job.file))
        
        # SETUP LICENSE
        # The base-class took care of selecting tags, we just check if we have to set up the 
        # interactive mode
        additional_args = list()
        if self.limit_nuke_interactive in cmd.tags:
            additional_args.append('-i')
            # make sure there is only one license - our overrides are additive, and this is a fix
            # to duplicate counts
            if self.limit_nuke_render in cmd.tags:
                cmd.tags.remove(self.limit_nuke_render)
            # end handle license
        # end handle interactive license
        
        cmd.args = cmd.args + [
            '-f',   # render full size, no proxy
            '-F %i-%i' % (data.frame.chunk.first, data.frame.chunk.last), # can do stepping as well: A-BxC
            '-V', '1', # be verbose, but not too verbose
            '-x', # execute script (rather than edit) 
            str(data.job.file)
        ] + additional_args
        
        ## allow retries in special situations, can be multiple ones
        cmd.retryrc = NukeTractorDelegate.read_error_return_code
        
        yield Task(title='nuke render', cmds = cmd)
        
# end class NukeRenderTaskGenerator


