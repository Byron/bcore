#-*-coding:utf-8-*-
"""
@package bqc.tests.doc.test_examples

@copyright 2012 Sebastian Thiel
"""
__all__ = []

import sys

import bcore
from butility.tests import (TestCaseBase,
                            with_rw_directory)

from bqc import (QualityCheckRunner,
                      QualityCheckBase)

## [quality_check]

class FileExistsCheck(QualityCheckBase):
    """Check if a file exists. When fixing, it just creates it"""

    __slots__ = (
                    '_file_path'  # path at which to create a file
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    _name = "File Exists Check"
    _description = "Check if a file exists. Create it as a fix if required"
    _can_fix = True
    
    ## -- End Configuration -- @}
    
    def __init__(self, file_path):
        super(FileExistsCheck, self).__init__()
        self._file_path = file_path
        
    def run(self):
        """Check the file exists"""
        self._result = self._file_path.isfile() and self.success or self.failure
        return super(FileExistsCheck, self).run()
        
    def fix(self):
        """create the missing file"""
        self._file_path.touch()
        return super(FileExistsCheck, self).fix()

# end class FileExistsCheck

## [quality_check]

class QualityCheckRunnerTest(QualityCheckRunner):
    """basic quality check runner, just inherits the QualityCheckRunner interface"""


class QualityCheckTest(TestCaseBase):
    """brief docs"""
    __slots__ = ()

    @with_rw_directory
    def test_check_run(self, rw_dir):
        """Show how to setup a check and run it"""
        
        ## [quality_check_usage]
        file_path = rw_dir / "some_file_i_require.ext"
        assert not file_path.exists()
        qck = FileExistsCheck(file_path)
        runner = QualityCheckRunnerTest([qck])
        # run without automatic fixing - the check will fail as the file does not exist
        runner.run_all()
        assert qck.result() is QualityCheckBase.failure, "qc didn't fail as expected"
        
        # re-run with fixing enabled
        runner.run_all(auto_fix=True)
        assert qck.result() is QualityCheckBase.success, "qc didn't succeed as expected"
        assert file_path.isfile(), "Now the file should exist"
        ## [quality_check_usage]
        
# end class QualityCheckTest

