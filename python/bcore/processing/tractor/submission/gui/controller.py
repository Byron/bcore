#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.submission.gui.controller
@brief Controllers to combine widgets into more complex user interfaces

@copyright 2013 Sebastian Thiel
"""
__all__ = ['TractorSubmissionController']

from PySide import (
                        QtGui,
                        QtCore
                    )

import bcore
from bcore.processing.tractor.alf.generators import (
                                                        JobGenerator,
                                                        MultiJobGenerator,
                                                  )

from . import widgets
from .ctrl_single_ui import Ui_SingleJob

from .widgets import TractorMessageDialog

log = service(bcore.ILog).new('bcore.processing.tractor.submission.gui.controller')


class TractorSubmissionController(QtGui.QWidget):
    """A controller which support single submission"""
    
    name = 'Submitool'
    version = '0.1.0'
    
    # -------------------------
    ## @name Initialization
    # @{
    
    def _connect_widgets(self):
        """Connect our widgets, wire them up to allow consistent results"""
        self.ui.selector.selection_changed.connect(self._chain_changed)
        self.ui.submit.submission_result.connect(self._submission_done)
        
    def _init_contents(self):
        """Fill generators and initial information"""
        # For now we insert JobGenerators here - in multi-mode this might be a multi-file generator
        self.setWindowTitle('%s (%s)' % (self.name, self.version))
        chains = list()
        JobGeneratorType = self._multifile_mode() and MultiJobGenerator or JobGenerator
        for chain in new_service(bcore.ITractorNodeGeneratorChainProvider).chains():
            chains.append(chain.prepend_head(JobGeneratorType()))
            if self._multifile_mode():
                # by default, we are in single-job mode - one job per button press
                chain.head().set_task_mode(True)
                chain.prepend_head(JobGenerator())
            # end handle additional structure
        #end for each chain 
        self.ui.selector.set_plugins(chains)
    
    ## -- End Initialization -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def init(self, keep_values_on_chain_change = True, initial_file_list = None):
        """Intiailize the controller and generate it's GUI.
        @return this instance
        @param keep_values_on_chain_change if True, values will be kept when changing chains. Otherwise, the
        default value will always be used.
        @param initial_file_list if set to a list of files, all of those will be batched. Otherwise it is up
        to the properties to set a file, if needed.
        @note to be called exactly once and before first use"""
        # For now, there is just one mode
        self.keep_values_on_chain_change = keep_values_on_chain_change
        self.file_list = initial_file_list or list()
        self.ui = Ui_SingleJob()
        self.ui.setupUi(self)
        self._connect_widgets()
        self._init_contents()
        return self
    
    ## -- End Interface -- @}
    
    
    # -------------------------
    ## @name Signals
    # @{
    
    ## Emitted when the controller is explicitly shutdown by a GUI event, for instance, after Job submission
    ## on user request
    shutdown = QtCore.Signal()
    
    ## -- End Signals -- @}
    
    # -------------------------
    ## @name Utiltiies
    # @{
    
    def _setup_files_context(self, context):
        """If we have any files stored and if the given context supports the job.files attribute, set our files
        accordingly for consumption"""
        if not self._multifile_mode():
            return
        # If we have files, we assume we have the right to set the static files info
        assert context.has_value('job.files'), "should have generator that injects this key"
        job = context.value_by_schema(MultiJobGenerator.static_field_schema)
        job.files = list(self.file_list)
        context.set_value_by_schema(MultiJobGenerator.static_field_schema, job)
        
    def _multifile_mode(self):
        """@return True if we are handling multiple input files"""
        return bool(self.file_list)
    
    ## -- End Utiltiies -- @}
    
    # -------------------------
    ## @name Slots
    # @{
    
    def _submission_done(self, job, jid, err):
        """Called when the submission was performed"""
        dialog = TractorMessageDialog(self)
        if err is not None:
            text = "Submission Failed!\n\n"
            text += str(err)
        else:
            text = "Submission Succeeded!\n\n"
            text += "Job is %s(%i)" % (job.title, jid)
        # end handle error
        dialog.ui.label.setText(text)
        dialog.finished.connect(self._on_dialog_close)
        dialog.show()
    
    def _chain_changed(self, gen):
        """Acts as a distributor for generators, as it sets up the chain widget, as well as the submit gui
        @param gen a generator chain, or None if there was nothing sleeted"""
        context = None
        if gen is not None:
            context = gen.default_context()
            self._setup_files_context(context)
        # end handle empty context
        
        # keep information during change
        if self.keep_values_on_chain_change:
            self.ui.properties.update_context(context)
        # end handle keep values
        self.ui.properties.set_chain(gen, context)
        
        # We assume we get only one job here, which is something we have to take care of
        job = None
        if context is not None:
            job = lambda: self.ui.properties.update_context(context) and gen.generator(context).next()
        # end handle context
        self.ui.submit.set_job(job)
        
    def _on_dialog_close(self, result):
        """Called when our modal dialog is closed"""
        if result == 0:
            self.shutdown.emit()
        # end handle close preseed or dialog cloesd
        
    ## -- End Slots -- @}
    
# end class TractorSubmissionController


