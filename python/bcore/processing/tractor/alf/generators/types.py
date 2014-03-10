#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.generators.types
@brief Implements actual types using the base classes

@copyright 2013 Sebastian Thiel
"""
__all__ = ['JobGenerator', 'MultiJobGenerator', 'FrameSequenceGenerator']

import bcore
from bcore.path import Path
from bcore.core.kvstore import (
                                KeyValueStoreSchema,
                                PathList
                            )
from bcore.utility import GraphIteratorBase

from ..types import (
                        StringChoice,
                        Job,
                        Task
                    )
from .base import (
                            NodeGeneratorBase,
                            SequenceGeneratorBase,
                            ValueSequenceGeneratorBase
                        )
                            


class JobGenerator(NodeGeneratorBase):
    """A generator producing a single Job alf operator based on its static fields, which pretty much correspond
    to the fields available in a Job operator.
    
    
    @note we are compatible to the MultiJobGenerator as we are setting the same variable_field_schema values that
    other generators can rely on
    @note instances of this type need to be at the start of the chain, as tractor requires Job objects to come first
    """
    __slots__ = ()
    
    static_field_schema = KeyValueStoreSchema('job', dict(
                                                         file = Path(''),   # the file the job takes as source
                                                         title = 'title',
                                                         comment = '',
                                                         metadata = '',
                                                         service = '',
                                                         
                                                     )
                                             )
    
    ## job.file: the current file we are processing
    variable_field_schema = KeyValueStoreSchema(static_field_schema.key(), dict(file = static_field_schema.file))
    
    def _tree_iterator(self, context):
        """@return a single job with our settings"""
        job_static = self._context_value(context, self.static_field_schema)
        # we assume that the schema keys match, job.file exists in static as well as in dynamic schema
        self._set_context_value(context, job_static, self.variable_field_schema)
        job = Job(title=job_static.title, comment=job_static.comment, metadata=job_static.metadata)
        if job_static.service:
            job.service = job_static.service
        # end handle tags
        yield job
        
# end class JobGenerator


class FrameSequenceGenerator(SequenceGeneratorBase):
    """Implements a generator for chunks of frames"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    static_field_schema = KeyValueStoreSchema('frame', dict(
                                                                first = 0.0,
                                                                last = 0.0,
                                                                step_size = 1.0,
                                                                chunk_size = 4.0,
                                                                ordering = StringChoice(SequenceGeneratorBase.ordering)
                                                            )
        
                            )
    
    variable_field_schema = KeyValueStoreSchema(static_field_schema.key(), dict(chunk = dict(
                                                                                            first = 0.0,
                                                                                            last = 0.0,
                                                                                            step = 1.0,
                                                                                            )
                                                                                )
                            )
    
    ## -- End Configuration -- @}
    
    def _tree_iterator(self, context):
        """Generate a task indicating the current frame range, for each available frame range
        @note we will modify the context to match the current chunk"""
        static_frame_data = self._context_value(context, self.static_field_schema)
        for first, last in self.chunks(context):
            # prepare context
            data = self._context_value(context)
            data.frame.chunk.first = first
            data.frame.chunk.last = last
            data.frame.chunk.step = static_frame_data.step_size
            self._set_context_value(context, data)
            
            prefix = 'frame'
            if first == last:
                title = prefix + ' %s' % first
            else:
                title = prefix + ' %s - %s' % (first, last)
            # end handle multi-frame
            
            yield Task(title)
        # end for each chunk
        
        
    # -------------------------
    ## @name Interface
    # @{
    
    def chunks(self, context):
        """@return a list of chunks, being a tuple of (first, last) float frames that will be used during generation.
        Each chunk defines an inclusive range of frames to be handled
        @param context a context with all static fields set for configuration"""
        chunks = list()
        frame = self._context_value(context, self.static_field_schema)
        cfirst = frame.first
        chunk_size = frame.chunk_size
        if chunk_size <= 0:
            chunk_size = frame.last - cfirst + frame.step_size
            if frame.chunk_size != 0.0:
                chunk_size = chunk_size / abs(frame.chunk_size)
            # end handle negative values
        # end handle chunk size
            
        while cfirst <= frame.last:
            clast = cfirst + chunk_size - frame.step_size
            if clast > frame.last:
                clast = frame.last
            # clamp range
            chunks.append((cfirst, clast > frame.last and frame.last or clast))
            cfirst += chunk_size
        # end for each step
        
        # APPLY ORDERING
        #################
        chunks = self._ordered_chunks(chunks, frame.ordering.selected())
        
        return chunks
        
    ## -- End Interface -- @}

# end class FrameSequenceGenerator


class MultiStringGeneratorBase(ValueSequenceGeneratorBase):
    """A type which allows to easily alternate and chunk strings with schema's entirely defined by subclasses
    """
    __slots__ = ()

    # -------------------------
    ## @name Subclass Interface
    # Useful to override certain class behavior
    # @{
    
    @bcore.abstractmethod
    def _set_strings_to_context(self, context, strings):
        """Called during _tree_iterator() evaluation to set the given list of strings into the 
        context according to the subclasses particular schema.
        This information can be read by generators downstream and used within commands for instance
        @param context containig all our data - it can be used to alter the way strings are handled
        @param strings a list of strings"""
        
    def _create_tree_operator(self, context, strings):
        """@return a tree node created according to the given context and list of strings, or None in case
        you don't want to create own structure
        @param context containing all our data - it can be used to alter the way the tree  is created, and was 
        set by _set_strings_to_context() beforehand
        @param strings a list of strings
        @note default implementation returns None"""
        
    ## -- End Subclass Interface -- @}
    
    def _tree_iterator(self, context):
        for strings in self.chunks(context):
            # update our variable chunk info
            self._set_strings_to_context(context, strings)
            tree = self._create_tree_operator(context, strings)
            if tree is not None:
                yield tree
        # end for each job file
    
    @bcore.abstractmethod
    def chunks(self, context):
        """@return A list of chunks of lists of strings to handle. Each chunk returned here will be worth 
        one tree iterator iteration. Its also valid to return a list of individual items.
        @param context a filled static context"""
        

# end class MultiJobGenerator


class MultiJobGenerator(MultiStringGeneratorBase):
    """A type without support for setting specific fields of a job, as it just takes a list of input files, 
    each corresponding to a single job.
    We currently enforce one file per job 
    """
    __slots__ = (
                    '_task_mode'    ## if True, we are in task mode. Otherwise its the job mode
                )

    # -------------------------
    ## @name Configuration
    # @{
    
    ## job.files: list of files we should generate jobs for
    ## job.files_per_chunk amount of files per chunk
    ## todo: use meta types
    static_field_schema = KeyValueStoreSchema(JobGenerator.static_field_schema.key(), 
                                                    dict(files = PathList(),
                                                          ordering = StringChoice(ValueSequenceGeneratorBase.ordering)
                                                       ))
    
    variable_field_schema = JobGenerator.variable_field_schema
    
    ## -- End Configuration -- @}
    
    
    def __init__(self, *args, **kwargs):
        super(MultiJobGenerator, self).__init__(*args, **kwargs)
        self._task_mode = False
    
    # -------------------------
    ## @name Subclass Interface
    # Useful to override certain class behavior
    # @{
    
    def _title(self, file):
        """@return a job title from the given job file"""
        return Path(file).basename()
        
    ## -- End Subclass Interface -- @}
    
    
    # -------------------------
    ## @name Interface
    # @{i
    
    def set_task_mode(self, state):
        """Set the task mode to the given one
        @param state if True, we will create Task instance instead of Job instance. This is useful
        if you want to have a single job with multiple subtasks, each corresponding to a particular file.
        Otherwise we will create a single Job operator per file
        @return self"""
        self._task_mode = state
        return self
    
    ## -- End Interface -- @}
    
    # -------------------------
    ## @name Subclass Implementation
    # @{
    
    def _create_tree_operator(self, context, file_path):
        TreeType = Job
        if self._task_mode:
            TreeType = Task
        # end handle task
        return TreeType(title = self._title(file_path))
        
    def _set_strings_to_context(self, context, file_path):
        data = self._context_value(context)
        data.job.file = file_path.abspath()
        self._set_context_value(context, data)
        
    ## -- End Subclass Implementation -- @}
    
    def chunks(self, context):
        """@return a list of individual job files, based on our static context information
        @param context a filled static context"""
        job = self._context_value(context, self.static_field_schema)
        chunks = self._value_chunks(job.files, 1, job.ordering.selected())
        
        # resolve list of lists to list of values
        return [chunk[0] for chunk in chunks]
        

# end class MultiJobGenerator

