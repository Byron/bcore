#-*-coding:utf-8-*-
"""
@package bcore.tests.processing.tractor.alf.test_generators
@brief tests for bcore.processing.tractor.alf.generators

@copyright 2013 Sebastian Thiel
"""

import sys
from StringIO import StringIO


from ..base import TractorTestCaseBase

from bcore.processing.tractor.alf import AlfSerializer
from bcore.processing.tractor.alf.generators import *


class TestGenerators(TractorTestCaseBase):
    """tests for alf task generators"""
    __slots__ = ()
    
    
    def test_jobgen(self):
        """testing of most fundamental features"""
        jgen = JobGenerator()
        context = jgen.default_context()
        data = context.value(jgen.static_field_schema.key(), jgen.static_field_schema)
        assert isinstance(data.title, str) and isinstance(data.comment, str) and isinstance(data.metadata, str)
        
        assert jgen.next() is None
        assert jgen.set_next(1).next() is 1
        assert jgen.set_next(None).next() is None
        
        
        data.title = 'foo'
        context.set_value(jgen.static_field_schema.key(), data)
        jgenit = jgen.generator(context) 
        job = jgenit.next()
        assert job.title == 'foo'
        self.failUnlessRaises(StopIteration, jgenit.next)
        
    def test_frame_gen(self):
        """test frame generator implementation"""
        fgen = FrameSequenceGenerator()
        context = fgen.default_context()
        frame = context.value(fgen.static_field_schema.key(), fgen.static_field_schema)
        
        frame.first = 1.0
        frame.last = 30
        
        frame.chunk_size = 4
        frame.ordering.set_selected_index(frame.ordering.index(fgen.ORDER_INVERSED))
        
        context.set_value(fgen.static_field_schema.key(), frame)
        
        chunks = fgen.chunks(context)
        assert len(list(fgen.generator(context))) == len(chunks)
        
        # check chunking
        assert chunks[0][0] == 29.0 and chunks[0][1] == 30.0
        assert chunks[-1][0] == 1.0 and chunks[-1][1] == 4.0
        assert chunks[-2][0] == 5.0 and chunks[-2][1] == 8.0
        
        # Check difficult values
        frame.chunk_size = 0
        context.set_value(fgen.static_field_schema.key(), frame)
        
        chunks = fgen.chunks(context)
        assert len(chunks) == 1, "0 creates one big chunk"
        assert chunks[0][0] == 1.0 and chunks[0][1] == 30
        
        # negative values
        frame.chunk_size = -3
        context.set_value(fgen.static_field_schema.key(), frame)
        
        chunks = fgen.chunks(context)
        assert len(chunks) == 3, "-3 creates three chunks"
        assert chunks[0][0] == 21.0 and chunks[0][1] == 30
        
    def test_multi_sequence_generator(self):
        """test the generator for sequences of strings"""
        jgen = MultiJobGenerator()
        context = jgen.default_context()
        
        job = context.value(jgen.static_field_schema.key(), jgen.static_field_schema)
        job.files = ['foo', 'bar', 'baz']
        job.ordering.set_selected_index(job.ordering.index(jgen.ORDER_INVERSED))
        context.set_value(jgen.static_field_schema.key(), job)
        
        chunks = jgen.chunks(context)
        assert len(chunks) == 3 and chunks[-1] == 'foo' and chunks[0] == 'baz'
        
        assert len(list(jgen.generator(context))) == len(chunks)
        
        # should be able to redo it with this context, even though it will change on the way
        assert len(list(jgen.generator(context))) == len(jgen.chunks(context)) == 3
        
    def test_chained_generators(self):
        """combine all generators we have into a very complex one"""
        jgen = MultiJobGenerator(FrameSequenceGenerator())
        
        context = jgen.default_context()
        
        schema = jgen.field_schema()
        data = context.value(jgen.static_field_schema.key(), schema)
        data.job.files = ['foo.ma', 'bar.nk', 'baz.katana']
        data.frame.first = 2.5
        data.frame.last = 34.5
        
        context.set_value(schema.key(), data)
        
        for job in jgen.generator(context):
            AlfSerializer().init(sys.stdout).serialize(job)
        # end for each job
        
        # Try multi-task mode
        jgen.set_task_mode(True)
        jgen = JobGenerator(jgen)
        job = context.value(jgen.static_field_schema.key(), jgen.static_field_schema)
        job.title = 'multi-file-job'
        context.set_value(jgen.static_field_schema.key(), job)
        
        jgenit = jgen.generator(context)
        AlfSerializer().init(sys.stdout).serialize(jgenit.next())
        
        # should only have on item
        self.failUnlessRaises(StopIteration, jgenit.next)
        
        
        chain = NodeGeneratorChainBase().set_head(jgen)
        assert chain.head() is jgen
        assert chain.tail() is not jgen and chain.tail() is not None
        other_gen = JobGenerator()
        chain.prepend_head(other_gen).head() is other_gen and other_gen.next() is jgen
        
        
        
        
        
