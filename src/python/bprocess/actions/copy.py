#-*-coding:utf-8-*-
"""
@package bprocess.actions.copy
@brief Basic copy action

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['CopyAction']

import bapp
from bkvstore import PathList
from butility import Path

from .base import PackageAction

        
class CopyAction(PackageAction, bapp.plugin_type()):
    """An action to copy a single file to a folder"""
    __slots__ = (
                    ## True if we wrote the file to the folder
                    '_wrote_destination_file',
                    ## True if we created the destination directory in the process
                    '_wrote_destination_dir'
                )

    action_schema = {   
                        'source' : PathList,
                        'destination' : Path
                    }

    type_name = 'copy'

    description = 'copy single files'


    def __init__(self, *args):
        super(CopyAction, self).__init__(*args)
        self._wrote_destination_file = False
        self._wrote_destination_dir = False

    # -------------------------
    ## @name Utilities
    # @{
    
    ## -- End Utilities -- @}

    def apply(self):
        if self._dry_run():
            return

        data = self.action_data
        
        assert not data.destination.isdir(), "Destination at %s is a directory, which cannot currently be handled for file-copying" % data.destination

        assert not data.destination.endswith('/'), "Destination can currently only be treated as file"
        
        # create directories if required
        dest_dir = data.destination.dirname()
        if not dest_dir.isdir():
            dest_dir.makedirs()
            self._wrote_destination_dir = True
        #END assure destination dir exists

        assert len(data.source) == 1, "Can currently only copy a single file !"
        source = data.source[0]
        
        self.log.info("Copying '%s' to '%s'" % (source, data.destination))
        source.copy(data.destination)
        self._wrote_destination_file = True
            
    def rollback(self):
        data = self.action_data
        if self._wrote_destination_file and data.destination.isfile():
            self.log.info("Removing previously copied destination file: %s", data.destination)
            data.destination.remove()
            self._wrote_destination_file = False
        #END handle destination
        
        if self._wrote_destination_dir:
            try:
                dirname = data.destination.dirname()
                while True:
                    dirname.rmdir()
                    self.log.info("Removed empty directory: %s", dirname)
                    dirname = dirname.dirname()
                #END loop until error
            except OSError:
                pass
            #END handle exception
            self._wrote_destination_dir = False
        #END handle dest dir removal

# end class CopyAction
