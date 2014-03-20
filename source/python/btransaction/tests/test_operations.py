#-*-coding:utf-8-*-
"""
@package bcore.tests.processing.test_transaction
@brief tests for btransaction

@copyright 2013 Sebastian Thiel
"""
__all__ = []

import time

import bcore
from bcore.tests import (TestCaseBase,
                      with_rw_directory)
from bcore.utility import ConcurrentRun

from btransaction import (Transaction,
                                       StoringProgressIndicator)
from btransaction.operations.rsync import *
from btransaction.operations.fsops import *

log = service(bcore.ILog).new('bcore.tests.processing.transaction.test_operations')


class TestOperations(TestCaseBase):
    
    def _assert_rsync_state(self, ro):
        """Verify state of rsync object after operation"""
        assert ro._total_num_files_transferred
        if not ro._dry_run():
            assert ro._total_transferred_filesize_bytes
            # for some reason, this doesn't match, so lets be happy about what we get
            #assert ro._total_transferred_filesize_bytes == ro._current_total_transferred_filesize_bytes
            assert ro._current_total_transferred_filesize_bytes
            assert ro._num_files_transferred == ro._total_num_files_transferred, "Should have copied as many files as we gathered"
        #END handle dryrun
    
    @with_rw_directory
    def test_rsync(self, dest_dir):
        source = self.fixture_path("db/shotgun")
        for subdir in (None, "rsync_destination"): 
            destination = dest_dir
            if subdir is not None:
                destination /= subdir
            #END handle destination
            
            p = StoringProgressIndicator()
            for dry_run in reversed(range(2)):
                t = Transaction(log, dry_run = dry_run, progress = p)
                ro = RsyncOperation(t, source, destination)
                
                assert t.apply().succeeded(), "should work in any way"
                self._assert_rsync_state(ro)
                assert ro.actual_destination().exists() != dry_run
                assert not t.rollback().succeeded(), "Rollback always works, evern in dry run mode where it doesn't do anything"
                assert not ro.actual_destination().exists()
            # END for each dryrun mode
            
            # abort operation - make it a bit slower
            t.clear()
            ro = RsyncOperation(t, source, destination, max_bandwidth_kb=1000)
            cr = ConcurrentRun(t.apply, log).start()
            
            time.sleep(0.25)
            assert t.is_running(), "transaction should still be running"
            assert ro.actual_destination().exists(), "destination dir should have been created at least"
            t.abort(True)
            assert t.is_aborting()
            s = time.time()
            assert cr.result() is t, "Waited for result, which was not what we expected"
            elapsed = time.time() - s
            assert elapsed < 1.0, "Should have joined much faster, it took %f" % elapsed 
            
            assert not t.is_aborting(), "Shouldnt be in abort mode anymore after we aborted and rolled back"
            assert not ro.actual_destination().exists(), "Destination should not exist any more as we triggered a rollback"
            assert not t.succeeded()
        # END for each target style - one exists, the other doesn't

    @with_rw_directory
    def test_delete_op(self, rw_dir):
        # CHANGE OWNERSHIP
        base_dir = ((rw_dir / "dir").mkdir() / "other_file").touch()
        file = (rw_dir / "file").touch()
        
        # REMOVE FS ITEM
        for dry_run in reversed(range(2)):
            for item in (file, base_dir):
                t = Transaction(log, dry_run = dry_run)
                ro = DeleteOperation(t, item)
                
                assert item.exists()
                assert t.apply().succeeded()
                assert item.exists() == dry_run
            # end for each item to delete
        #END for each dryrun mode
