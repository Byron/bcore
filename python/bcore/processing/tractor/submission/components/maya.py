#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.components.maya
@brief Submission of maya scenes for rendering or for performing batch operations

@note This module needs to be usable anywhere, and may not rely on being run from the nuke host application
@copyright 2013 Sebastian Thiel
"""
__all__ = ['MayaBatchTaskChain', 'FrameSequenceMayaBatchTaskChain',  'FrameSequenceMayaRenderTaskChain']

from ...alf.generators import (
                                    NodeGeneratorChainBase,
                                    FrameSequenceGenerator,
                                    MayaRenderTaskGenerator, 
                                    MayaBatchTaskGenerator
                              )

class MayaBatchTaskChain(NodeGeneratorChainBase, Plugin):
    """A chain which just generates MayaBatch commands, without support for chunking"""
    __slots__ = ()
    
    def __init__(self):
        """Setup chain"""
        super(MayaBatchTaskChain, self).__init__()
        self.set_head(MayaBatchTaskGenerator())
        
    _plugin_name = "Maya Batch"

# end class MayaBatchTaskChain


class FrameSequenceMayaBatchTaskChain(NodeGeneratorChainBase, Plugin):
    """A chain which comes with support for chunking"""
    __slots__ = ()

    def __init__(self):
        """Setup chain with FrameSequenceGenerator"""
        super(FrameSequenceMayaBatchTaskChain, self).__init__()
        self.set_head(FrameSequenceGenerator(MayaBatchTaskGenerator()))
        
    _plugin_name = "Maya Batch (Chunked)"
        
# end class FrameSequenceMayaBatchTaskChain


class FrameSequenceMayaRenderTaskChain(NodeGeneratorChainBase, Plugin):
    """Describes a chain with frame sequence support useful for rendering with maya"""
    __slots__ = ()
    
    def __init__(self):
        """Setup chain with FrameSequenceGenerator"""
        super(FrameSequenceMayaRenderTaskChain, self).__init__()
        self.set_head(FrameSequenceGenerator(MayaRenderTaskGenerator()))
        
    _plugin_name = "Maya Render"
    
# end class FrameSequenceMayaRenderTaskChain

