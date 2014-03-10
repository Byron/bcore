#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.gui.widgets
@brief A selection of widgets to deal with submitting jobs

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorSubmissionWidget', 'TractorSelectorWidget', 'TractorMessageDialog', 
           'TractorGeneratorChainPropertiesWidget']


import bcore
from bcore.gui.widgets import PluginSelectorWidget
from bcore.gui import remove_widget_children
from PySide import (
                        QtGui,
                        QtCore
                    )
from bcore.processing.tractor.alf import Job
from bcore.processing.tractor.alf.generators import (
                                                    JobGenerator,
                                                    FrameSequenceGenerator,
                                                 )
from bcore.processing.tractor.submission import (
                                                TractorSubmitter,
                                                TractorJobID
                                            )
from . import ui
from .properties import GeneratorPropertiesWidgetBase

log = service(bcore.ILog).new('bcore.processing.tractor.submission.gui')


class TractorSubmissionWidget(QtGui.QWidget):
    """A widget for use with the TractorSubmitter, it serves as GUI for its interface and can be hooked up
    to other Widgets using signals and slots"""
    
    def __init__(self, *args):
        """Initialize this widget"""
        super(TractorSubmissionWidget, self).__init__(*args)
        self._job = None
        
        self.ui = ui.Ui_SubmitWidget()
        self.ui.setupUi(self)
        self._init_static_elements()
        
    # -------------------------
    ## @name Initialization
    # @{
    
    def _init_static_elements(self):
        """Intiailize gui elements which shouldn't change when our data changes"""
        priority = self.ui.priority
        for index, prio in enumerate(TractorSubmitter.priorities):
            priority.addItem(prio)
            if prio == TractorSubmitter.PRIORITY_NORMAL:
                priority.setCurrentIndex(index)
            # end handle default index
        # end for each prio
        
        # connections
        self.ui.submit.clicked.connect(self._on_submit_clicked)
    
    ## -- End Initialization -- @}
    
    
    # -------------------------
    ## @name Signals
    # @{
    
    ## Emitted once the given job was submitted
    ## If submission failed, TractorJobID will be -1, and err will be the exception,
    ## otherwise it will be the actual Job ID
    ## f(job_instance, tractor_id, exception=None) 
    submission_result = QtCore.Signal(Job, TractorJobID, object)
    
    ## -- End Signals -- @}
    
    
    # -------------------------
    ## @name Slots
    # @{
    
    def set_job(self, job):
        """Set the given job to be used when the submit-button is clicked.
        @param job either an alf Job instance, or None to indicate no job is ready for submission.
        Can also be a callable, which is expected to produce an alf Job. It will be called right before submission.
        This should be use to hand in generator functions that generate jobs based on some context, for instance
        @note if the controller wants to prevent resubmission, it should change the job to None after submission
        @note will reset any generator/context, see set_generator
        """
        self._job = job
        self.ui.submit.setEnabled(job is not None)
        
    def _on_submit_clicked(self, *args):
        """Handle the button press"""
        assert self._job, 'need a job'
        submitter = TractorSubmitter()
        
        jid = TractorJobID(TractorJobID.invalid)
        err = None
        try:
            job = self._job
            if callable(job):
                job = job()
            # end produce job
            jid = submitter.submit(job, priority = self.ui.priority.currentText(), 
                                              paused = self.ui.paused.isChecked())
        except Exception, exc:
            log.error('error during submission', exc_info = True)
            err = exc
        # end ignore invalid submission
        
        self.submission_result.emit(job, jid, err)
        
    ## -- End Slots -- @}

# end class TractorSubmissionWidget


class TractorSelectorWidget(PluginSelectorWidget):
    """Utility type to make using promoted widgets in designer easier"""
    
# end class TractorSelectorWidget


class TractorGeneratorChainPropertiesWidget(QtGui.QWidget):
    """A dynamic GUI which shows any amount of know chain items, using its own mapping of widgets
    
    As long as we don't have a generalized GUI to work with KVStores, we have to do it like that and map
    individual gui elements to someting in a kvstore. This is done by the widgets, we are just here
    to map them put them into a common layout
    """
    
    def __init__(self, *args):
        """Intiialize our layout"""
        super(TractorGeneratorChainPropertiesWidget, self).__init__(*args)
        
        self._context = None
        self.vlayout = QtGui.QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(4)
        self.set_chain(None, None)
        
    # -------------------------
    ## @name Utilities
    # @{
    
    def _clear_widgets(self):
        """Empty all our widgets by deleting them, clears the layout"""
        # remove all children of our widget - this also removes the layout
        remove_widget_children(self, lambda child: child is not self.vlayout) 
    
    ## -- End Utilities -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def set_chain(self, chain, context):
        """Set our instance to display the given chain, using the given context as data source
        GUI will be initialized from the given context's values based on known Generators found in the chain.
        Generators are visualized by mapping respective GUI elements to them, which in turn are used to 
        write their values back into the data set.
        @param chain a NodeGeneratorChainBase compatible instance, or None which is when this instance will 
        be cleared.
        @param context KeyValueStore retrieved from the given chain, or None to clear this instance.
        @return the chain's context we are representing, as retrieved by chain.default_context()"""
        self._clear_widgets()
        widget_types = bcore.environment.classes(GeneratorPropertiesWidgetBase)
        self._context = context
        
        if chain is None or context is None:
            label = QtGui.QLabel(self)
            label.setText("Nothing to display")
            label.setAlignment(QtCore.Qt.AlignCenter)
            self.layout().addWidget(label)
            return
        # end handle clearing
        
        # Create GUI elements
        generator = chain.head()
        while generator:
            # If we have a widget, show it, otherwise bail out
            for cls in widget_types:
                if cls.is_compatible(generator):
                    widget = cls(type(generator).__name__, self)
                    assert generator.static_field_schema, "generators with gui need a static field schema"
                    widget.init(generator, context.value_by_schema(generator.static_field_schema))
                    
                    self.layout().addWidget(widget)
                    # make sure we get only one !
                    break
                # end if widget is compatible
            # end for each widget type
            generator = generator.next()
        # end for each generator
        
        # Finally make sure it is stuck to the top
        self.layout().addItem(QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
        
    def update_context(self, context):
        """Update the given context with our widget's data
        @return this instance"""
        for widget in self.children():
            if not isinstance(widget, GeneratorPropertiesWidgetBase):
                continue
            # end if its not the correct widget type
            widget.save_to(context)
        # end for each child widget
        return self
        
    ## -- End Interface -- @}

# end class GeneratorChainWidget


class TractorMessageDialog(QtGui.QDialog):
    """Simple message dialog suitable for us
    @todo might not make too much sense to customize this"""
    
    def __init__(self, *args):
        """brief docs"""
        super(TractorMessageDialog, self).__init__(*args)
        self.ui = ui.Ui_MessageDialog()
        self.ui.setupUi(self)

# end class TractorMessageDialog
