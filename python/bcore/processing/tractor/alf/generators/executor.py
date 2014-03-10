#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf.generators.executor
@brief A generator for jobs executing anything on the farm with stdin piping support

@copyright 2013 Sebastian Thiel
"""
__all__ = ['BashExecuteTaskGenerator', 'ExecuteTaskGenerator']

from bcore.core.kvstore import KeyValueStoreSchema
from .cmdbase import TractorCmdGeneratorBase
from .. import Task
from bcore.utility import DictObject

class ExecuteTaskGenerator(TractorCmdGeneratorBase):
    """Create a task which can feed any input to stdin of a command
    
    @note the command substitutes everything available in the context into your commandline, i.e. -file {job.file}
    will work just fine
    """
    __slots__ = ()
    
    
    # -------------------------
    ## @name Configuration
    # @{
    
    static_field_schema = KeyValueStoreSchema('batch', dict(executable = str(),    # path to executable
                                                            args = str(),          # additional arguments as string
                                                            stdincmd = str(),      # if set, it will be fed to STDIN           
                                                           )
                                               )
    
    ## -- End Configuration -- @}
    
    def _is_valid_context(self, context):
        """Check our context for required values"""
        data = self._context_value(context)
        
        if not data.batch.executable:
            return False
        
        return super(ExecuteTaskGenerator, self)._is_valid_context(context)
    
    def _tree_iterator(self, context):
        batch = self._context_value(context, self.static_field_schema)
        assert batch.executable, 'executable needs to be set'
        
        substitution_data = DictObject(context.data())
        cmd = self._cmd_type()(batch.executable, batch.args.format(**substitution_data))
        
        if batch.stdincmd:
            cmd.msg = batch.stdincmd.format(**substitution_data)
        # end handle stdin
        
        yield Task(title=batch.executable, cmds = cmd)

# end class ExecuteTaskGenerator


class BashExecuteTaskGenerator(ExecuteTaskGenerator):
    """Executes bash commands"""
    __slots__ = ()
    
    _bash_location = '/bin/bash'
    
    def _default_context(self):
        """@return context with filled in bash location"""
        context = super(BashExecuteTaskGenerator, self)._default_context()
        batch = context.value_by_schema(self.static_field_schema)
        
        batch.executable = self._bash_location
        
        context.set_value_by_schema(self.static_field_schema, batch)
        return context

# end class BashExecuteTaskGenerator
