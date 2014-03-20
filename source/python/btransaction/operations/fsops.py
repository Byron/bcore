#-*-coding:utf-8-*-
"""
@package bcore.transaction.operations.fsops
@brief A package for trivial filesystem operations that can be combined within a transaction

@copyright 2013 Sebastian Thiel
"""
__all__ = ['DeleteOperation']

from ..base import Operation
from butility import Path


class DeleteOperation(Operation):
    """Delete a file or a directory. Please note that, for obvious reasons, failures
    cannot be undone. This operation will stop at the first encountered error"""
    
    __slots__ = "_path"     # the path to delete
    name = "DeleteOperation"
    
    def __init__(self, transaction, path):
        super(DeleteOperation, self).__init__(transaction)
        self._path = Path(path)
        
    def apply(self):
        if self._dry_run():
            return
        
        if self._path.isdir():
            self.log.info("Deleting directory %s", self._path)
            self._path.rmtree()
        else:
            self.log.info("Deleting file %s", self._path)
            self._path.remove()
        #END perform actual removal
        
    def rollback(self):
        self.log.info("Deletion of filesystem items cannot be rolled back")
    
