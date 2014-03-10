#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.components.nuke
@brief Job Submission plugins

@copyright 2013 Sebastian Thiel
"""
__all__ = ['NukeRenderTasksChain']


from ...alf.generators import (
                                NodeGeneratorChainBase,
                                FrameSequenceGenerator,
                                NukeRenderTaskGenerator
                              )


class NukeRenderTasksChain(NodeGeneratorChainBase, Plugin):
    """Represents a generator chain which is preconfigured to support frame chunking as and simple rendering
    of all enabled write nodes in a script.
    
    @note for compatibility, its important not to include the Job generator in this chain
    """
    __slots__ = ()
    
    def __init__(self):
        """Setup the chain"""
        super(NukeRenderTasksChain, self).__init__()
        self.set_head(FrameSequenceGenerator(NukeRenderTaskGenerator()))
        
    _plugin_name = "Nuke Render"
        
# end class NukeRenderTasksChain


