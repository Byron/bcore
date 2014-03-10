#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.components.bash
@brief Implements a chain for bash-batching, but it can possibly be used for anything

@copyright 2013 Sebastian Thiel
"""
__all__ = ['BashTaskChain', 'ChunkedBashTaskChain']

from ...alf.generators import (
                                NodeGeneratorChainBase,
                                FrameSequenceGenerator,
                                BashExecuteTaskGenerator
                             )

class BashTaskChain(NodeGeneratorChainBase, Plugin):
    """Simple bash batch commands, for now without chunking."""
    __slots__ = ()
    
    def __init__(self):
        """Setup chain"""
        super(BashTaskChain, self).__init__()
        self.set_head(BashExecuteTaskGenerator())
        
    _plugin_name = "Bash Execution"

# end class MayaBatchTaskChain


class ChunkedBashTaskChain(NodeGeneratorChainBase, Plugin):
    """Simple bash batch commands with chunking support"""
    __slots__ = ()
    
    def __init__(self):
        """Setup chain"""
        super(ChunkedBashTaskChain, self).__init__()
        self.set_head(BashExecuteTaskGenerator())
        self.prepend_head(FrameSequenceGenerator())
        
    _plugin_name = "Bash Execution (Chunked)"

# end class ChunkedBashTaskChain




