#-*-coding:utf-8-*-
"""
@package bapp.transaction.operations.fsops
@brief A package for trivial filesystem operations that can be combined within a transaction

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['DeleteOperation', 'CreateFSItemOperation', 'MoveFSItemOperation', ]

from ..base import Operation
from butility import Path
import os

class FSOperationBase(Operation):
    __slots__ = "_operation_performed"
    
    description = "Perform a filesystem operation"
    
    def __init__(self, transaction):
        super(FSOperationBase, self).__init__(transaction)
        self._reset_state()
        
    def _reset_state(self):
        self._operation_performed = False
        
    @classmethod
    def _assert_posix(cls):
        """Raise on non-posix systems"""
        if os.name != "posix":
            raise AssertionError("This module only works on posix systems")
        #END handle posix


    @classmethod
    def set_user_group(cls, path, uid = None, gid = None):
        """Set the uid and/or gid of the given path. If one of the items is None, 
        it will deal properly with the issue and only change what needs to be changed """
        if uid is not None or gid is not None:
            if not (uid and gid):
                stat = os.stat(path)
                uid = uid is not None and uid or stat.st_uid
                gid = gid is not None and gid or stat.st_gid
            #END get info
            path.chown(uid, gid)
        #END if we should change the access mode


class CreateFSItemOperation(FSOperationBase):
    """Create a directory or file with the given access permissions and ownership. In
    case of a file, you may specify an initial content.
    For this operation to succeed, the destination path must not exist yet!"""
    __slots__ = ("_path", "_content", "_mode", "_uid", "_gid")
    
    name = "CreateFSItem"
    
    def __init__(self, transaction, path, initial_file_content = None, mode=None, uid=None, gid=None):
        """Initialize the operation with a path to create. If initial_file_content is set, 
        to a string, it will be written in binary mode to a file. If it is unset, 
        a directory will be created. Non-existing parent-directories will be created.
        After creation, the mode will be set if not None, and uid and gid will be set as well to the given
        numerical ID if of of them is not None"""
        super(CreateFSItemOperation, self).__init__(transaction)
        self._assert_posix()
        self._path = Path(path)
        self._content = initial_file_content
        self._mode = mode
        self._uid = uid
        self._gid = gid
        
    def apply(self):
        if self._content and self._path.isdir() or not self._content and self._path.isfile():
            raise AssertionError("Cannot create item of type directory or file as the an equally named item of different type exists")
        #END sanity check

        if self._dry_run():
            return

        if self._path.exists():
            return
        # end ignore existing items of the same type
        
        # we don't do it the most efficient way, as we could specify certain things in 
        # at creation. For now, we don't do it though as it shouldn't matter
        if self._content:
            self.log.info("creating file  %s", self._path)
            self._path.write_bytes(self._content)
        else:
            self.log.info("creating directory %s", self._path)
            self._path.makedirs()
        #END initial creation
        self._operation_performed = True
        
        
        if self._mode is not None:
            self._path.chmod(self._mode)
        #END handle mode
        
        self.set_user_group(self._path, self._gid, self._uid)
        
    def rollback(self):
        try:
            if not self._operation_performed or not self._path.exists():
                return
                
            if self._content:
                self.log.info("Removing file %s", self._path)
                self._path.remove()
            else:
                self.log.info("Removing single directory %s", self._path)
                self._path.rmdir()
            #END handle removal, safely as we don't recursively delete anything
        finally:
            self._reset_state()
        

class MoveFSItemOperation(FSOperationBase):
    """Move a file or directory to the given name"""
    __slots__ = ("_source_path", "_destination_path", "_actual_destination_path")
    
    name = "FSItemMove"
    
    def __init__(self, transaction, source_path, destination_path):
        super(MoveFSItemOperation, self).__init__(transaction)
        self._source_path = Path(source_path).expandvars()
        self._destination_path = self._actual_destination_path = Path(destination_path).expandvars()
        
        # if we move into a directory, the filename will just be appended
        if self._destination_path.isdir():
            self._actual_destination_path = self._destination_path / source_path.basename()
        # END handle actual destination

    def apply(self):
        if self._actual_destination_path.exists():
            raise AssertionError("Cannot move item %s onto existing one at %s" % (self._source_path, self._actual_destination_path))
        #END handle existing dsetination
        
        if self._dry_run():
            return
        
        self.log.info("moving %s to %s", self._source_path, self._destination_path)
        self._source_path.move(self._destination_path)
        self._operation_performed = True
        
    def rollback(self):
        try:
            if not self._operation_performed or not self._actual_destination_path.exists():
                return
            
            # fail gracefully
            if self._source_path.exists():
                raise AssertionError("Cannot move destination %s into existing source %s, source directory should not exist" % (self._actual_destination_path, self._source_path))
            self.log.info("moving %s to %s", self._actual_destination_path, self._source_path)
            self._actual_destination_path.move(self._source_path)
        finally:
            self._reset_state()
        #END assure state reset
        
    #{ Interface
    
    def actual_destination(self):
        """:return: path to the final destination"""
        return self._actual_destination_path
        
    #} END interface


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
    
