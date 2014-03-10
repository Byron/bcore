#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.gui.properties
@brief Widgets dealing with properties for ChainGenerators

@copyright 2013 Sebastian Thiel
"""
__all__ = ['GeneratorPropertiesWidgetBase', 'FrameSequenceGeneratorPropertiesWidget', 'JobGeneratorPropertiesWidget',
           'MayaRenderPropertiesWidget', 'MayaBatchPropertiesWidget']

from PySide import QtGui

import bcore
from bcore.path import Path
from bcore.processing.tractor.alf.generators import (
                                                    JobGenerator,
                                                    MultiJobGenerator,
                                                    FrameSequenceGenerator,
                                                    MayaBatchTaskGenerator,
                                                    MayaRenderTaskGenerator,
                                                    ExecuteTaskGenerator
                                                )
from . import ui

# ==============================================================================
## @name ChainWidgets
# ------------------------------------------------------------------------------
# Property sheets for chain generators
## @{

class GeneratorPropertiesWidgetBase(QtGui.QGroupBox):
    """A base class for widgets that are compatible to the TractorGeneratorChainWidget"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Subclasses should set this to the type of generator they support so that is_compatible is handled() 
    # correctly automatically
    CompatibleGeneratorType = None
    
    ## Underlying UI class to setup
    UIType = None
    
    ## -- End Configuration -- @}
    
    
    def __init__(self, *args):
        """Initialize some instance values"""
        super(GeneratorPropertiesWidgetBase, self).__init__(*args)
        self._data = None   # our data block
        self._generator = None # corresponding generator
        assert self.UIType is not None, 'Subclass must set its UIType'
        self.ui = self.UIType()
        self.ui.setupUi(self)
        self._post_setup()
        
    # -------------------------
    ## @name Subclass Interface
    # @{
    
    def _post_setup(self):
        """Called after the setup of our widgets from ui definition is complete. Use this callback
        to setup custom widgets, or additinoal connections"""
        
    
    def _from_data(self, data):
        """Initialize your gui elements from the given datablock, matching the static_field_schema of your
        generator"""
        raise NotImplemented("subclass implementation required")
        
    def _to_data(self, data):
        """Write values from your gui into the given datablock
        @see _from_data"""
        raise NotImplemented("subclass implementation required")
    
    ## -- End Subclass Interface -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def is_compatible(cls, generator):
        """@return True if this widget can handle displaying the context of a generator of the given type"""
        assert cls.CompatibleGeneratorType is not None, "subclass has to set CompatibleGeneratorType"
        return isinstance(generator, cls.CompatibleGeneratorType)
    
    def init(self, generator, data):
        """Initialize your widgets from the given context, using data retrieved from the given generator's
        static_field_schema.
        @param generator the TaskGenerator instance we should represent. Its used to obtain schemas from it 
        @param data DictObject as retrieved from the actual context using the static_field_schema of the generator.
        Currently you are restricted to those values
        @return this instance"""
        self._generator = generator
        self._data = data
        self._from_data(data)
        return self
        
    def save_to(self, context):
        """Save your gui state into the data you previously obtained (in init()) and write it back into the context
        @param context context into which to write your data
        @return self"""
        self._to_data(self._data)
        context.set_value_by_schema(self._generator.static_field_schema, self._data)
        return self
        
    ## -- End Interface -- @}

# end class GeneratorPropertiesWidgetBase


class FrameSequenceGeneratorPropertiesWidget(GeneratorPropertiesWidgetBase):
    """Handles chunk controls"""
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## If True, an additional combobox, .chunk, will be hidden by default.
    # Use it to implement application specific chunk sources
    hide_chunksource = True
    
    ## -- End Configuration -- @}
    
    CompatibleGeneratorType = FrameSequenceGenerator
    UIType = ui.Ui_FrameSequenceBox
    
    
    def __init__(self, *args):
        """Make sure the source field is hidden by default"""
        super(FrameSequenceGeneratorPropertiesWidget, self).__init__(*args)
        
    def _post_setup(self):
        """setup hidden items"""
        if self.hide_chunksource:
            self.ui.source.setHidden(True)
            self.ui.source_label.setHidden(True)
        # end handle chunksource
        return super(FrameSequenceGeneratorPropertiesWidget, self)._post_setup()
        
    
    def _from_data(self, frame):
        self.ui.first.setValue(frame.first)
        self.ui.last.setValue(frame.last)
        self.ui.step_size.setValue(frame.step_size)
        self.ui.chunk_size.setValue(frame.chunk_size)
        for order in frame.ordering:
            self.ui.order.addItem(order)
        # end handle order
        self.ui.order.setCurrentIndex(frame.ordering.selected_index())
        
    def _to_data(self, frame):
        frame.first = self.ui.first.value()
        frame.last = self.ui.last.value()
        frame.step_size = self.ui.step_size.value()
        frame.chunk_size = self.ui.chunk_size.value()
        frame.ordering.set_selected_index(self.ui.order.currentIndex())
    
# end class FrameSequenceGeneratorPropertiesWidget


class JobGeneratorPropertiesWidget(GeneratorPropertiesWidgetBase):
    """Handles job controls"""
    
    CompatibleGeneratorType = JobGenerator
    UIType = ui.Ui_JobGeneratorBox
    
    def __init__(self, *args):
        """Assure comment field is initially hidden"""
        super(JobGeneratorPropertiesWidget, self).__init__(*args)
        self.ui.advanced_widget.setHidden(True)
    
    def _from_data(self, job):
        self.ui.title.setText(job.title)
        self.ui.file.setText(str(job.file))
        self.ui.comment.setText(job.comment)
        self.ui.service.setText(job.service)
        if job.comment or job.service:
            self.ui.advanced.setChecked(True)
            self.ui.advanced_widget.setVisible(True)
        # end handle advanced
        
    def _to_data(self, job):
        job.title = self.ui.title.text()
        job.file = self.ui.file.text()
        job.comment = self.ui.comment.toPlainText()
        job.service = self.ui.service.text()
        
# end class FrameSequenceGeneratorPropertiesWidget


class MultiTaskPropertiesWidget(GeneratorPropertiesWidgetBase):
    """A widget to display the input files"""
    __slots__ = ()
    
    CompatibleGeneratorType = MultiJobGenerator
    UIType = ui.Ui_MultiTaskGeneratorBox

    def _from_data(self, job):
        self.ui.files.clear()
        for file in job.files:
            self.ui.files.addItem(str(file))
        # end for each file
        self.ui.info.setText("File to submit: %i" % len(job.files))
        
    def _to_data(self, job):
        files = list()
        for fid in range(self.ui.files.count()):
            files.append(Path(self.ui.files.item(fid).text()))
        #end for each file id

# end class MultiTaskPropertiesWidget


class MayaBatchPropertiesWidget(GeneratorPropertiesWidgetBase):
    """Handles maya batch controls"""
    
    CompatibleGeneratorType = MayaBatchTaskGenerator
    UIType = ui.Ui_MayaBatchBox
    
    def _from_data(self, maya):
        self.ui.cmdpython.setText(maya.cmd.python)
        
    def _to_data(self, maya):
        maya.cmd.python = self.ui.cmdpython.toPlainText()
        
# end class FrameSequenceGeneratorPropertiesWidget


class ExecutorPropertiesWidget(GeneratorPropertiesWidgetBase):
    """Handles executor controls"""
    
    CompatibleGeneratorType = ExecuteTaskGenerator
    UIType = ui.Ui_ExecuteGeneratorBox
    
    def _from_data(self, batch):
        self.ui.executable.setText(batch.executable)
        self.ui.args.setText(batch.args)
        self.ui.stdincmd.setText(batch.stdincmd)
        
    def _to_data(self, batch):
        batch.executable = self.ui.executable.text()
        batch.args = self.ui.args.text()
        batch.stdincmd = self.ui.stdincmd.toPlainText()
        
# end class FrameSequenceGeneratorPropertiesWidget


class MayaRenderPropertiesWidget(GeneratorPropertiesWidgetBase):
    """Handles maya render controls"""
    
    CompatibleGeneratorType = MayaRenderTaskGenerator
    UIType = ui.Ui_MayaRenderBox
    
    def _from_data(self, maya):
        self.ui.image_output_directory.setText(maya.render.image_output_directory)
        
    def _to_data(self, maya):
        maya.render.image_output_directory = self.ui.image_output_directory.text()
        
# end class FrameSequenceGeneratorPropertiesWidget

# can't use Plugin due to bogus metaclass layout conflict
for widget in ( FrameSequenceGeneratorPropertiesWidget,
                JobGeneratorPropertiesWidget,
                MayaBatchPropertiesWidget,
                MayaRenderPropertiesWidget,
                MultiTaskPropertiesWidget,  # must come after frameSequence widget
                ExecutorPropertiesWidget,):
    bcore.environment.register(widget)
# end for each widget

## -- End ChainWidgets -- @}
