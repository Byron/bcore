#-*-coding:utf-8-*-
"""
@package bcore.tests.processing.tractor
@brief tests for bcore.processing.tractor

@copyright 2013 Sebastian Thiel
"""
__all__ = []

from .base import TractorTestCaseBase

from bcore.processing.tractor.delegates import NukeTractorDelegate


class TestDelegates(TractorTestCaseBase):
    """Tests for delegates of all kinds"""
    __slots__ = ()
        
    def test_nuke_delegate(self):
        """Test delegate log parsing capabilities"""
        logfile = self.fixture_path("nuke_readerror.log")
        assert logfile.isfile()
        
        delegate = NukeTractorDelegate()
        exit_status_seen_count = 0
        for line in open(logfile):
            res, value = delegate._classifiy_line(line.strip())
            exit_status_seen_count += res == NukeTractorDelegate.LINE_FATAL
        # end for each line
        assert exit_status_seen_count == 3, "should have parsed the status exactly three times"
# end class TestDelegates
